# Techbleat Banking Frontend — runtime configuration

The original auth.js and App.jsx logic is preserved except for replacing Vite build-time values with `window.__BANKING_CONFIG__`.

## Source changes
Copy the included `techbleat-global-bank-frontend/` files into the same paths in your repository.
`public/config.js` provides local development defaults. `index.html` loads it before the Vite application.

## First build
Commit/build/publish a **new image tag** (e.g. `ghcr.io/techbleat/banking-frontend:v2`).

## Kubernetes
1. `kubectl apply -f kubernetes/frontend-runtime-config.yaml`
2. Add a `runtime-config` volume to the existing `frontend` Deployment:

```yaml
spec:
  template:
    spec:
      volumes:
        - name: runtime-config
          configMap:
            name: banking-frontend-runtime
```

3. In the existing frontend container `volumeMounts`, add:

```yaml
- name: runtime-config
  mountPath: /usr/share/nginx/html/config.js
  subPath: config.js
  readOnly: true
```

Keep all your existing volume mounts, services, and Nginx proxy rules; **merge** these snippets, don't replace the lists.

4. In the existing frontend Nginx ConfigMap's `server` block, add:

```nginx
location = /config.js {
    default_type application/javascript;
    add_header Cache-Control "no-store, max-age=0" always;
}
```

5. Update the Deployment image to your published tag and apply the revised manifest.

## Verify
`curl -fsS http://localhost:3000/config.js`
`curl -fsS http://localhost:3000/ | grep config.js`
Browser login should redirect to `https://auth.techbleat-training.com/realms/banking/...`.

ConfigMap mounts using `subPath` need a Deployment rollout to pick up updates.
Client ID/roles/URLs are public client settings. Never store secrets in config.js.
