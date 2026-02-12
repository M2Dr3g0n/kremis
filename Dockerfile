# ---- Build ----
FROM rust:1.89-slim AS build
WORKDIR /src
COPY Cargo.toml Cargo.lock ./
COPY crates/ crates/
COPY apps/ apps/
RUN cargo build --release -p kremis && strip target/release/kremis

# ---- Runtime ----
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN groupadd -r kremis && useradd -r -g kremis kremis
COPY --from=build /src/target/release/kremis /usr/local/bin/kremis
RUN mkdir -p /data && chown kremis:kremis /data
USER kremis
WORKDIR /data
EXPOSE 8080
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8080/health || exit 1
ENTRYPOINT ["kremis"]
CMD ["server", "-H", "0.0.0.0", "-D", "/data/kremis.db"]
