# Stand-in for a Vite build. In a real project stage one runs `npm ci &&
# npm run build` with `base: '/beta/'` configured, and stage two copies the
# built assets into nginx. The runtime image below is what matters here:
# static files served by nginx, nothing else in the image.
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY public /usr/share/nginx/html
