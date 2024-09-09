FROM aiod_metadata_catalogue
RUN python -m pip install alembic
ENV PYTHONPATH="$PYTHONPATH:/app"
WORKDIR /alembic
ENTRYPOINT ["alembic", "upgrade", "head"]
