#!/usr/bin/env node
const { Server } = require('@modelcontextprotocol/sdk/server');
const { DefaultAzureCredential } = require('@azure/identity');
const { SecretClient } = require('@azure/keyvault-secrets');

class AzureKeyVaultServer {
    constructor() {
        this.server = new Server(
            {
                name: 'azure-keyvault-server',
                version: '0.1.0',
            },
            {
                capabilities: {
                    tools: {},
                },
            }
        );

        this.setupToolHandlers();
        this.server.onerror = (error) => console.error('[MCP Error]', error);
        
        // Initialize Azure Key Vault and fetch OpenAI key on startup
        this.initializeKeyVault();
    }

    async initializeKeyVault() {
        try {
            const credential = new DefaultAzureCredential();
            const vaultUrl = 'https://kmc.vault.azure.net';
            const client = new SecretClient(vaultUrl, credential);
            
            // Fetch OpenAI API key and set it as environment variable
            const secret = await client.getSecret('OpenAIkmckeyvault1');
            process.env.AZURE_KV_OPENAI_KEY = secret.value;
            console.error('Successfully fetched OpenAI API key from Azure Key Vault');
        } catch (error) {
            console.error('Failed to fetch OpenAI API key from Azure Key Vault:', error.message);
            process.exit(1);
        }
    }

    setupToolHandlers() {
        this.server.setRequestHandler('ListToolsRequestSchema', async () => ({
            tools: [
                {
                    name: 'get_secret',
                    description: 'Get a secret from Azure Key Vault',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            vaultName: {
                                type: 'string',
                                description: 'Name of the Azure Key Vault',
                            },
                            secretName: {
                                type: 'string',
                                description: 'Name of the secret to retrieve',
                            },
                        },
                        required: ['vaultName', 'secretName'],
                    },
                },
            ],
        }));

        this.server.setRequestHandler('CallToolRequestSchema', async (request) => {
            if (request.params.name !== 'get_secret') {
                throw new Error(`Unknown tool: ${request.params.name}`);
            }

            const { vaultName, secretName } = request.params.arguments;
            const credential = new DefaultAzureCredential();
            const vaultUrl = `https://${vaultName}.vault.azure.net`;
            const client = new SecretClient(vaultUrl, credential);

            try {
                const secret = await client.getSecret(secretName);
                return {
                    content: [
                        {
                            type: 'text',
                            text: secret.value,
                        },
                    ],
                };
            } catch (error) {
                return {
                    content: [
                        {
                            type: 'text',
                            text: `Error retrieving secret: ${error.message}`,
                        },
                    ],
                    isError: true,
                };
            }
        });
    }

    async run() {
        const transport = new (require('@modelcontextprotocol/sdk/server/stdio')).StdioServerTransport();
        await this.server.connect(transport);
        console.error('Azure Key Vault MCP server running on stdio');
    }
}

const server = new AzureKeyVaultServer();
server.run().catch(console.error);
