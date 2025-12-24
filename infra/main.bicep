// main.bicep - Azure DB Zone Redundancy Benchmark Infrastructure
// Deploys VNet, VM, and database resources for benchmarking

@description('Azure region for deployment')
param location string = 'centralus'

@description('Unique suffix for resource names (e.g., random string or timestamp)')
param nameSuffix string = uniqueString(resourceGroup().id)

@description('Admin username for VM and databases')
param adminUsername string = 'benchadmin'

@description('Admin password for databases')
@secure()
param adminPassword string

@description('SSH public key for VM authentication')
param sshPublicKey string

@description('VM size for the benchmark client')
param vmSize string = 'Standard_D4s_v5'

@description('PostgreSQL SKU name')
param postgresSkuName string = 'Standard_D4ds_v5'

@description('PostgreSQL storage size in GB')
param postgresStorageGB int = 128

@description('MySQL SKU name')
param mysqlSkuName string = 'Standard_D4ads_v5'

@description('MySQL storage size in GB')
param mysqlStorageGB int = 128

@description('Azure SQL DTU capacity (for General Purpose, this is vCores)')
param sqlVCores int = 4

@description('Azure SQL storage size in GB')
param sqlStorageGB int = 128

@description('Primary availability zone for VM and all database servers (1, 2, or 3)')
param primaryZone string = '1'

@description('Standby availability zone for cross-zone HA databases')
param standbyZone string = '2'

// Variables
var vnetName = 'vnet-zrbench-${nameSuffix}'
var vmSubnetName = 'snet-vm'
var dbSubnetName = 'snet-db'
var vmName = 'vm-bench-${nameSuffix}'
var publicIpName = 'pip-bench-${nameSuffix}'
var nicName = 'nic-bench-${nameSuffix}'
var nsgName = 'nsg-bench-${nameSuffix}'
var managedIdentityName = 'id-bench-${nameSuffix}'

// PostgreSQL server names
var pgNonHaName = 'pg-noha-${nameSuffix}'
var pgSameZoneHaName = 'pg-szha-${nameSuffix}'
var pgCrossZoneHaName = 'pg-czha-${nameSuffix}'

// MySQL server names
var mysqlNonHaName = 'mysql-noha-${nameSuffix}'
var mysqlSameZoneHaName = 'mysql-szha-${nameSuffix}'
var mysqlCrossZoneHaName = 'mysql-czha-${nameSuffix}'

// Azure SQL names
var sqlServerName = 'sql-zrbench-${nameSuffix}'
var sqlDbNonZrName = 'sqldb-nonzr'
var sqlDbZrName = 'sqldb-zr'

// User Assigned Managed Identity
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: managedIdentityName
  location: location
}

// Network Security Group
resource nsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: nsgName
  location: location
  properties: {
    securityRules: [
      {
        name: 'AllowSSH'
        properties: {
          priority: 1000
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '22'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'AllowPostgreSQL'
        properties: {
          priority: 1100
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '5432'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'AllowMySQL'
        properties: {
          priority: 1200
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '3306'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'AllowSQLServer'
        properties: {
          priority: 1300
          direction: 'Outbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '1433'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}

// Virtual Network
resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: vmSubnetName
        properties: {
          addressPrefix: '10.0.1.0/24'
          networkSecurityGroup: {
            id: nsg.id
          }
        }
      }
      {
        name: dbSubnetName
        properties: {
          addressPrefix: '10.0.2.0/24'
          delegations: [
            {
              name: 'Microsoft.DBforPostgreSQL.flexibleServers'
              properties: {
                serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers'
              }
            }
          ]
        }
      }
      {
        name: 'snet-mysql'
        properties: {
          addressPrefix: '10.0.3.0/24'
          delegations: [
            {
              name: 'Microsoft.DBforMySQL.flexibleServers'
              properties: {
                serviceName: 'Microsoft.DBforMySQL/flexibleServers'
              }
            }
          ]
        }
      }
      {
        name: 'snet-sql'
        properties: {
          addressPrefix: '10.0.4.0/24'
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

// Private DNS Zones
resource privateDnsZonePostgres 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.postgres.database.azure.com'
  location: 'global'
}

resource privateDnsZoneMysql 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink.mysql.database.azure.com'
  location: 'global'
}

resource privateDnsZoneSql 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: 'privatelink${environment().suffixes.sqlServerHostname}'
  location: 'global'
}

// VNet Links for Private DNS Zones
resource vnetLinkPostgres 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: privateDnsZonePostgres
  name: 'link-postgres'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnet.id
    }
  }
}

resource vnetLinkMysql 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: privateDnsZoneMysql
  name: 'link-mysql'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnet.id
    }
  }
}

resource vnetLinkSql 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: privateDnsZoneSql
  name: 'link-sql'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnet.id
    }
  }
}

// Public IP for VM
resource publicIp 'Microsoft.Network/publicIPAddresses@2023-11-01' = {
  name: publicIpName
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
    publicIPAddressVersion: 'IPv4'
  }
}

// Network Interface for VM
resource nic 'Microsoft.Network/networkInterfaces@2023-11-01' = {
  name: nicName
  location: location
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          subnet: {
            id: '${vnet.id}/subnets/${vmSubnetName}'
          }
          privateIPAllocationMethod: 'Dynamic'
          publicIPAddress: {
            id: publicIp.id
          }
        }
      }
    ]
  }
}

// Cloud-init script for VM setup
var cloudInitScript = '''
#cloud-config
package_update: true
package_upgrade: true

packages:
  - python3.11
  - python3.11-venv
  - python3-pip
  - git
  - curl
  - wget
  - unzip
  - postgresql-client
  - mysql-client
  - jq

runcmd:
  # Install Azure CLI
  - curl -sL https://aka.ms/InstallAzureCLIDeb | bash

  # Install ODBC Driver 18 for SQL Server
  - curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
  - curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
  - apt-get update
  - ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 unixodbc-dev
  - echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> /etc/profile.d/mssql-tools.sh
  - chmod +x /etc/profile.d/mssql-tools.sh

  # Create benchmark directory
  - mkdir -p /opt/benchmark
  - chown ${adminUsername}:${adminUsername} /opt/benchmark

  # Create results directory
  - mkdir -p /opt/benchmark/results
  - chown ${adminUsername}:${adminUsername} /opt/benchmark/results

  # Set Python 3.11 as default
  - update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
  - update-alternatives --set python3 /usr/bin/python3.11
'''

// Virtual Machine
resource vm 'Microsoft.Compute/virtualMachines@2024-03-01' = {
  name: vmName
  location: location
  zones: [primaryZone]
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    hardwareProfile: {
      vmSize: vmSize
    }
    storageProfile: {
      imageReference: {
        publisher: 'Canonical'
        offer: '0001-com-ubuntu-server-jammy'
        sku: '22_04-lts-gen2'
        version: 'latest'
      }
      osDisk: {
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: 'Premium_LRS'
        }
        diskSizeGB: 128
      }
    }
    osProfile: {
      computerName: vmName
      adminUsername: adminUsername
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: {
          publicKeys: [
            {
              path: '/home/${adminUsername}/.ssh/authorized_keys'
              keyData: sshPublicKey
            }
          ]
        }
      }
      customData: base64(cloudInitScript)
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: nic.id
        }
      ]
    }
  }
}

// PostgreSQL Flexible Server - Non-HA
resource pgNonHa 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: pgNonHaName
  location: location
  sku: {
    name: postgresSkuName
    tier: 'GeneralPurpose'
  }
  properties: {
    version: '16'
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    availabilityZone: primaryZone
    storage: {
      storageSizeGB: postgresStorageGB
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      delegatedSubnetResourceId: '${vnet.id}/subnets/${dbSubnetName}'
      privateDnsZoneArmResourceId: privateDnsZonePostgres.id
    }
  }
  dependsOn: [
    vnetLinkPostgres
  ]
}

// PostgreSQL Flexible Server - SameZone HA
resource pgSameZoneHa 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: pgSameZoneHaName
  location: location
  sku: {
    name: postgresSkuName
    tier: 'GeneralPurpose'
  }
  properties: {
    version: '16'
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    availabilityZone: primaryZone
    storage: {
      storageSizeGB: postgresStorageGB
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'SameZone'
    }
    network: {
      delegatedSubnetResourceId: '${vnet.id}/subnets/${dbSubnetName}'
      privateDnsZoneArmResourceId: privateDnsZonePostgres.id
    }
  }
  dependsOn: [
    vnetLinkPostgres
    pgNonHa // Deploy sequentially to avoid conflicts
  ]
}

// PostgreSQL Flexible Server - CrossZone HA (Zone Redundant)
resource pgCrossZoneHa 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: pgCrossZoneHaName
  location: location
  sku: {
    name: postgresSkuName
    tier: 'GeneralPurpose'
  }
  properties: {
    version: '16'
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    availabilityZone: primaryZone
    storage: {
      storageSizeGB: postgresStorageGB
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'ZoneRedundant'
      standbyAvailabilityZone: standbyZone
    }
    network: {
      delegatedSubnetResourceId: '${vnet.id}/subnets/${dbSubnetName}'
      privateDnsZoneArmResourceId: privateDnsZonePostgres.id
    }
  }
  dependsOn: [
    vnetLinkPostgres
    pgSameZoneHa // Deploy sequentially to avoid conflicts
  ]
}

// PostgreSQL Databases
resource pgNonHaDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  parent: pgNonHa
  name: 'benchmark'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource pgSameZoneHaDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  parent: pgSameZoneHa
  name: 'benchmark'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource pgCrossZoneHaDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  parent: pgCrossZoneHa
  name: 'benchmark'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// MySQL Flexible Server - Non-HA
resource mysqlNonHa 'Microsoft.DBforMySQL/flexibleServers@2023-12-30' = {
  name: mysqlNonHaName
  location: location
  sku: {
    name: mysqlSkuName
    tier: 'GeneralPurpose'
  }
  properties: {
    version: '8.0.21'
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    availabilityZone: primaryZone
    storage: {
      storageSizeGB: mysqlStorageGB
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      delegatedSubnetResourceId: '${vnet.id}/subnets/snet-mysql'
      privateDnsZoneResourceId: privateDnsZoneMysql.id
    }
  }
  dependsOn: [
    vnetLinkMysql
  ]
}

// MySQL Flexible Server - SameZone HA
resource mysqlSameZoneHa 'Microsoft.DBforMySQL/flexibleServers@2023-12-30' = {
  name: mysqlSameZoneHaName
  location: location
  sku: {
    name: mysqlSkuName
    tier: 'GeneralPurpose'
  }
  properties: {
    version: '8.0.21'
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    availabilityZone: primaryZone
    storage: {
      storageSizeGB: mysqlStorageGB
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'SameZone'
    }
    network: {
      delegatedSubnetResourceId: '${vnet.id}/subnets/snet-mysql'
      privateDnsZoneResourceId: privateDnsZoneMysql.id
    }
  }
  dependsOn: [
    vnetLinkMysql
    mysqlNonHa // Deploy sequentially to avoid conflicts
  ]
}

// MySQL Flexible Server - CrossZone HA (Zone Redundant)
resource mysqlCrossZoneHa 'Microsoft.DBforMySQL/flexibleServers@2023-12-30' = {
  name: mysqlCrossZoneHaName
  location: location
  sku: {
    name: mysqlSkuName
    tier: 'GeneralPurpose'
  }
  properties: {
    version: '8.0.21'
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    availabilityZone: primaryZone
    storage: {
      storageSizeGB: mysqlStorageGB
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'ZoneRedundant'
      standbyAvailabilityZone: standbyZone
    }
    network: {
      delegatedSubnetResourceId: '${vnet.id}/subnets/snet-mysql'
      privateDnsZoneResourceId: privateDnsZoneMysql.id
    }
  }
  dependsOn: [
    vnetLinkMysql
    mysqlSameZoneHa // Deploy sequentially to avoid conflicts
  ]
}

// MySQL Databases
resource mysqlNonHaDb 'Microsoft.DBforMySQL/flexibleServers/databases@2023-12-30' = {
  parent: mysqlNonHa
  name: 'benchmark'
  properties: {
    charset: 'utf8mb4'
    collation: 'utf8mb4_unicode_ci'
  }
}

resource mysqlSameZoneHaDb 'Microsoft.DBforMySQL/flexibleServers/databases@2023-12-30' = {
  parent: mysqlSameZoneHa
  name: 'benchmark'
  properties: {
    charset: 'utf8mb4'
    collation: 'utf8mb4_unicode_ci'
  }
}

resource mysqlCrossZoneHaDb 'Microsoft.DBforMySQL/flexibleServers/databases@2023-12-30' = {
  parent: mysqlCrossZoneHa
  name: 'benchmark'
  properties: {
    charset: 'utf8mb4'
    collation: 'utf8mb4_unicode_ci'
  }
}

// Azure SQL Logical Server
resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: sqlServerName
  location: location
  properties: {
    administratorLogin: adminUsername
    administratorLoginPassword: adminPassword
    version: '12.0'
    publicNetworkAccess: 'Disabled'
    minimalTlsVersion: '1.2'
  }
}

// Azure SQL Database - Non-Zone Redundant
resource sqlDbNonZr 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: sqlDbNonZrName
  location: location
  sku: {
    name: 'GP_Gen5'
    tier: 'GeneralPurpose'
    capacity: sqlVCores
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: int(sqlStorageGB) * 1024 * 1024 * 1024
    zoneRedundant: false
  }
}

// Azure SQL Database - Zone Redundant
resource sqlDbZr 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: sqlDbZrName
  location: location
  sku: {
    name: 'GP_Gen5'
    tier: 'GeneralPurpose'
    capacity: sqlVCores
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: int(sqlStorageGB) * 1024 * 1024 * 1024
    zoneRedundant: true
  }
}

// Private Endpoint for Azure SQL
resource sqlPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-11-01' = {
  name: 'pe-sql-${nameSuffix}'
  location: location
  properties: {
    subnet: {
      id: '${vnet.id}/subnets/snet-sql'
    }
    privateLinkServiceConnections: [
      {
        name: 'sql-connection'
        properties: {
          privateLinkServiceId: sqlServer.id
          groupIds: [
            'sqlServer'
          ]
        }
      }
    ]
  }
}

// Private DNS Zone Group for SQL
resource sqlPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-11-01' = {
  parent: sqlPrivateEndpoint
  name: 'sqlDnsZoneGroup'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'config'
        properties: {
          privateDnsZoneId: privateDnsZoneSql.id
        }
      }
    ]
  }
}

// Outputs
output vmPublicIp string = publicIp.properties.ipAddress
output vmName string = vmName
output vmSshCommand string = 'ssh ${adminUsername}@${publicIp.properties.ipAddress}'

output postgresNonHaHost string = pgNonHa.properties.fullyQualifiedDomainName
output postgresSameZoneHaHost string = pgSameZoneHa.properties.fullyQualifiedDomainName
output postgresCrossZoneHaHost string = pgCrossZoneHa.properties.fullyQualifiedDomainName

output mysqlNonHaHost string = mysqlNonHa.properties.fullyQualifiedDomainName
output mysqlSameZoneHaHost string = mysqlSameZoneHa.properties.fullyQualifiedDomainName
output mysqlCrossZoneHaHost string = mysqlCrossZoneHa.properties.fullyQualifiedDomainName

output sqlServerHost string = sqlServer.properties.fullyQualifiedDomainName
output sqlDbNonZrName string = sqlDbNonZrName
output sqlDbZrName string = sqlDbZrName

output adminUsername string = adminUsername
output nameSuffix string = nameSuffix
