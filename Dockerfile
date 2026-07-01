# =============================================================================
# Custom image: postgis/postgis:18-3.6 (PostgreSQL 18 + PostGIS 3.6, prebuilt)
# + pg_partman built from source (no official image exists for pg_partman,
#   so this compiles it inside the build stage instead of asking you to do it
#   by hand on the host).
# =============================================================================
FROM postgis/postgis:18-3.6

# pg_partman version to build. Check https://github.com/pgpartman/pg_partman/releases
# for the latest tag if you want a newer version than this default.
ARG PG_PARTMAN_VERSION=5.2.4

# Build dependencies needed to compile the extension against PG18's server headers.
# postgresql-server-dev-18 must match the major version of the base image exactly.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        postgresql-server-dev-18 \
        wget \
        ca-certificates \
    && wget -q "https://github.com/pgpartman/pg_partman/archive/refs/tags/v${PG_PARTMAN_VERSION}.tar.gz" \
        -O /tmp/pg_partman.tar.gz \
    && mkdir -p /tmp/pg_partman \
    && tar -xzf /tmp/pg_partman.tar.gz -C /tmp/pg_partman --strip-components=1 \
    && cd /tmp/pg_partman \
    && make NO_BGW=0 \
    && make install \
    # Clean up build deps to keep the final image smaller — extension files are
    # already installed into PostgreSQL's share/extension and lib directories,
    # so the compiler toolchain is no longer needed at runtime.
    && apt-get purge -y --auto-remove build-essential postgresql-server-dev-18 wget \
    && rm -rf /var/lib/apt/lists/* /tmp/pg_partman /tmp/pg_partman.tar.gz

# Required for pg_partman's background worker (the bgw binary built above) to be
# loaded at server startup — this is the step that's awkward to do manually on a
# bare-metal host, since it needs a postgresql.conf edit + restart. Baking it into
# the image means it's already correct every time the container starts.
RUN echo "shared_preload_libraries = 'pg_partman_bgw'" >> /usr/share/postgresql/postgresql.conf.sample \
    && echo "pg_partman_bgw.interval = 3600" >> /usr/share/postgresql/postgresql.conf.sample \
    && echo "pg_partman_bgw.role = 'postgres'" >> /usr/share/postgresql/postgresql.conf.sample \
    && echo "pg_partman_bgw.dbname = 'bus_enterprise'" >> /usr/share/postgresql/postgresql.conf.sample