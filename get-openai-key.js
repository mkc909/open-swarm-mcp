const { DefaultAzureCredential } = require("@azure/identity");
const { SecretClient } = require("@azure/keyvault-secrets");

async function getOpenAIKey() {
    try {
        const credential = new DefaultAzureCredential();
        const vaultUrl = "https://kmc.vault.azure.net";
        const client = new SecretClient(vaultUrl, credential);
        
        const secret = await client.getSecret("OpenAIkmckeyvault1");
        console.log(secret.value);
    } catch (error) {
        console.error("Error fetching secret:", error.message);
        process.exit(1);
    }
}

getOpenAIKey();
