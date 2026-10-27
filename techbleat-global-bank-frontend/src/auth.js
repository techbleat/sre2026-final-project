import Keycloak from "keycloak-js";

// config.js is loaded before the React application by index.html.
const config = window.__BANKING_CONFIG__;
if (!config?.keycloakUrl || !config?.keycloakRealm || !config?.keycloakClientId) {
  throw new Error("Banking runtime configuration is missing or incomplete (config.js).");
}

const clientId = config.keycloakClientId;
const keycloak = new Keycloak({
  url: config.keycloakUrl,
  realm: config.keycloakRealm,
  clientId,
});

let initialization;

export function initializeAuth() {
  if (!initialization) {
    initialization = keycloak.init({
      onLoad: "check-sso",
      pkceMethod: "S256",
      checkLoginIframe: false,
    });
  }
  return initialization;
}

export function login() {
  return keycloak.login({ redirectUri: `${window.location.origin}/` });
}

export async function getAccessToken() {
  if (!keycloak.authenticated) {
    throw new Error("Your session has expired. Please sign in again.");
  }
  await keycloak.updateToken(30);
  return keycloak.token;
}

export function getIdentity() {
  return keycloak.tokenParsed || null;
}

export function hasRole(role) {
  if (!role || !keycloak.tokenParsed) return false;
  const claims = keycloak.tokenParsed;
  const realmRoles = claims.realm_access?.roles || [];
  const clientRoles = claims.resource_access?.[clientId]?.roles || [];
  return realmRoles.includes(role) || clientRoles.includes(role);
}

export function logout() {
  return keycloak.logout({ redirectUri: window.location.origin });
}