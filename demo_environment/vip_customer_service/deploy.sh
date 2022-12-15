heroku login
heroku container:login
heroku container:push web --app norkos-vip-customer
heroku container:release web --app norkos-vip-customer
heroku logs --app norkos-vip-customer