// Local-development defaults. Kubernetes overrides this file using a ConfigMap.
// Never put credentials or other secrets in browser configuration.
window.__BANKING_CONFIG__ = {
  keycloakUrl: "http://localhost:8080",
  keycloakRealm: "banking",
  keycloakClientId: "banking-frontend",
  bankingViewRole: "banking-customer",
  bankingTransactionRole: "banking-transact",
  bankingAiAgentRole: "banking-ai-agent"
};
