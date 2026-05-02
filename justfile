set dotenv-load

dumpenv:
    op inject -i env.example -o .env

# launch docs server
docs:
    zensical serve --dev-addr localhost:8002

# upload to pypi
publish:
    uv build && \
    uv publish --token $PYPI_TOKEN
