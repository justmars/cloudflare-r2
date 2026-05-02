dumpenv:
  op inject -i env.example -o .env

# launch docs server
docs:
  zensical serve --dev-addr localhost:8001
