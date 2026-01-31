//! # Kremis SDK - The Kit
//!
//! SDK for building Kremis plugins.
//!
//! Plugins are external processes that communicate with the Kremis server via HTTP.
//! This SDK provides type-safe wrappers for the HTTP API.
//!
//! ## Quick Start
//!
//! ```rust,ignore
//! use kremis_sdk::{KremisClient, Signal};
//!
//! #[tokio::main]
//! async fn main() -> Result<(), kremis_sdk::Error> {
//!     let client = KremisClient::new("http://localhost:8080");
//!
//!     // Check health
//!     let health = client.health().await?;
//!     println!("Server status: {}", health.status);
//!
//!     // Ingest a signal
//!     let signal = Signal::new(1, "temperature", "25.0");
//!     let result = client.ingest(&signal).await?;
//!     println!("Ingested to node: {:?}", result.node_id);
//!
//!     // Query the graph
//!     let status = client.status().await?;
//!     println!("Graph has {} nodes", status.node_count);
//!
//!     Ok(())
//! }
//! ```
//!
//! ## Plugin Architecture
//!
//! ```text
//! ┌─────────────────────┐          HTTP           ┌─────────────────────┐
//! │   Your Plugin       │ ◄───────────────────►   │   Kremis Server     │
//! │   (Python/Rust)     │                         │   (apps/kremis)     │
//! │                     │                         │                     │
//! │  ┌───────────────┐  │  POST /signal           │  ┌───────────────┐  │
//! │  │ kremis-sdk    │  │  POST /query            │  │ kremis-core   │  │
//! │  │ (optional)    │  │  GET /status            │  │ (THE LOGIC)   │  │
//! │  └───────────────┘  │  GET /stage             │  └───────────────┘  │
//! └─────────────────────┘  POST /export           └─────────────────────┘
//! ```

use serde::{Deserialize, Serialize};
use thiserror::Error;

// =============================================================================
// ERROR TYPE
// =============================================================================

/// Errors from the Kremis SDK.
#[derive(Debug, Error)]
pub enum Error {
    /// HTTP request failed.
    #[error("HTTP error: {0}")]
    Http(#[from] reqwest::Error),

    /// JSON serialization/deserialization failed.
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    /// Server returned an error response.
    #[error("Server error: {0}")]
    Server(String),
}

// =============================================================================
// SIGNAL TYPE
// =============================================================================

/// A signal to ingest into the graph.
///
/// Signals follow the [Entity | Attribute | Value] format per AGENTS.md.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Signal {
    pub entity_id: u64,
    pub attribute: String,
    pub value: String,
}

impl Signal {
    /// Create a new signal.
    pub fn new(entity_id: u64, attribute: impl Into<String>, value: impl Into<String>) -> Self {
        Self {
            entity_id,
            attribute: attribute.into(),
            value: value.into(),
        }
    }

    /// Create a new signal with validation on field lengths.
    ///
    /// # Errors
    ///
    /// Returns [`Error::Server`] if:
    /// - `attribute` is empty or exceeds 256 bytes
    /// - `value` is empty or exceeds 65,536 bytes
    pub fn try_new(
        entity_id: u64,
        attribute: impl Into<String>,
        value: impl Into<String>,
    ) -> Result<Self, Error> {
        let attribute = attribute.into();
        let value = value.into();
        if attribute.is_empty() || attribute.len() > 256 {
            return Err(Error::Server(format!(
                "Attribute length {} out of valid range 1..=256",
                attribute.len()
            )));
        }
        if value.is_empty() || value.len() > 65536 {
            return Err(Error::Server(format!(
                "Value length {} out of valid range 1..=65536",
                value.len()
            )));
        }
        Ok(Self {
            entity_id,
            attribute,
            value,
        })
    }
}

// =============================================================================
// RESPONSE TYPES
// =============================================================================

/// Health check response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
}

/// Graph status response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatusResponse {
    pub node_count: usize,
    pub edge_count: usize,
    pub stable_edges: usize,
    pub density_millionths: u64,
}

/// Stage response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StageResponse {
    pub stage: String,
    pub name: String,
    pub progress_percent: u8,
    pub stable_edges_needed: usize,
    pub stable_edges_current: usize,
}

/// Ingest response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IngestResponse {
    pub success: bool,
    pub node_id: Option<u64>,
    pub error: Option<String>,
}

/// Query response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueryResponse {
    pub success: bool,
    pub found: bool,
    pub path: Vec<u64>,
    pub edges: Vec<Edge>,
    pub error: Option<String>,
}

/// Edge in query response.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Edge {
    pub from: u64,
    pub to: u64,
    pub weight: i64,
}

// =============================================================================
// QUERY TYPES
// =============================================================================

/// Query request types.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Query {
    Lookup {
        entity_id: u64,
    },
    Traverse {
        node_id: u64,
        depth: usize,
    },
    TraverseFiltered {
        node_id: u64,
        depth: usize,
        min_weight: i64,
    },
    StrongestPath {
        start: u64,
        end: u64,
    },
    Intersect {
        nodes: Vec<u64>,
    },
    Related {
        node_id: u64,
        depth: usize,
    },
}

// =============================================================================
// CLIENT
// =============================================================================

/// HTTP client for the Kremis server.
///
/// This client provides type-safe access to all Kremis HTTP endpoints.
#[derive(Debug, Clone)]
pub struct KremisClient {
    base_url: String,
    client: reqwest::Client,
}

impl KremisClient {
    /// Create a new client connecting to the given base URL.
    ///
    /// # Example
    ///
    /// ```rust,ignore
    /// let client = KremisClient::new("http://localhost:8080");
    /// ```
    pub fn new(base_url: impl Into<String>) -> Self {
        Self {
            base_url: base_url.into(),
            client: reqwest::Client::builder()
                .timeout(std::time::Duration::from_secs(30))
                .build()
                .unwrap_or_default(),
        }
    }

    /// Create a new client with API key authentication.
    ///
    /// Sends `Authorization: Bearer <api_key>` with every request
    /// and applies a 30-second timeout.
    ///
    /// # Errors
    ///
    /// Returns [`Error::Server`] if the API key contains invalid header characters,
    /// or [`Error::Network`] if the HTTP client fails to build.
    ///
    /// # Example
    ///
    /// ```rust,ignore
    /// let client = KremisClient::with_api_key("http://localhost:8080", "my-secret-key");
    /// ```
    pub fn with_api_key(base_url: impl Into<String>, api_key: &str) -> Result<Self, Error> {
        use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION};
        let mut headers = HeaderMap::new();
        let value = HeaderValue::from_str(&format!("Bearer {}", api_key))
            .map_err(|e| Error::Server(format!("Invalid API key header: {}", e)))?;
        headers.insert(AUTHORIZATION, value);
        let client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .default_headers(headers)
            .build()?;
        Ok(Self {
            base_url: base_url.into(),
            client,
        })
    }

    /// Health check.
    ///
    /// # Errors
    ///
    /// Returns [`Error::Network`] if the server is unreachable.
    pub async fn health(&self) -> Result<HealthResponse, Error> {
        let url = format!("{}/health", self.base_url);
        let resp = self.client.get(&url).send().await?.json().await?;
        Ok(resp)
    }

    /// Get graph status.
    ///
    /// # Errors
    ///
    /// Returns [`Error::Network`] on connection failure or [`Error::Server`] on auth error.
    pub async fn status(&self) -> Result<StatusResponse, Error> {
        let url = format!("{}/status", self.base_url);
        let resp = self.client.get(&url).send().await?.json().await?;
        Ok(resp)
    }

    /// Get developmental stage.
    ///
    /// # Errors
    ///
    /// Returns [`Error::Network`] on connection failure or [`Error::Server`] on auth error.
    pub async fn stage(&self) -> Result<StageResponse, Error> {
        let url = format!("{}/stage", self.base_url);
        let resp = self.client.get(&url).send().await?.json().await?;
        Ok(resp)
    }

    /// Ingest a signal.
    ///
    /// # Errors
    ///
    /// Returns [`Error::Server`] if the signal is invalid or ingestion fails.
    pub async fn ingest(&self, signal: &Signal) -> Result<IngestResponse, Error> {
        let url = format!("{}/signal", self.base_url);
        let resp: IngestResponse = self
            .client
            .post(&url)
            .json(signal)
            .send()
            .await?
            .json()
            .await?;

        if !resp.success {
            if let Some(err) = &resp.error {
                return Err(Error::Server(err.clone()));
            }
        }

        Ok(resp)
    }

    /// Execute a query.
    ///
    /// # Errors
    ///
    /// Returns [`Error::Server`] if the query is invalid or execution fails.
    pub async fn query(&self, query: &Query) -> Result<QueryResponse, Error> {
        let url = format!("{}/query", self.base_url);
        let resp: QueryResponse = self
            .client
            .post(&url)
            .json(query)
            .send()
            .await?
            .json()
            .await?;

        if !resp.success {
            if let Some(err) = &resp.error {
                return Err(Error::Server(err.clone()));
            }
        }

        Ok(resp)
    }

    /// Lookup an entity by ID.
    ///
    /// # Errors
    ///
    /// Returns [`Error::Network`] on connection failure or [`Error::Server`] on query error.
    pub async fn lookup(&self, entity_id: u64) -> Result<Option<u64>, Error> {
        let resp = self.query(&Query::Lookup { entity_id }).await?;
        Ok(resp.path.first().copied())
    }

    /// Traverse from a node.
    pub async fn traverse(&self, node_id: u64, depth: usize) -> Result<QueryResponse, Error> {
        self.query(&Query::Traverse { node_id, depth }).await
    }

    /// Find the strongest path between two nodes.
    pub async fn strongest_path(&self, start: u64, end: u64) -> Result<Vec<u64>, Error> {
        let resp = self.query(&Query::StrongestPath { start, end }).await?;
        Ok(resp.path)
    }
}

// =============================================================================
// CONVENIENCE FUNCTIONS
// =============================================================================

/// Create multiple signals from a list of tuples.
///
/// # Example
///
/// ```rust
/// use kremis_sdk::signals;
///
/// let signals = signals![
///     (1, "temperature", "25.0"),
///     (2, "humidity", "60%"),
///     (3, "pressure", "1013hPa"),
/// ];
/// ```
#[macro_export]
macro_rules! signals {
    [$(($entity:expr, $attr:expr, $val:expr)),* $(,)?] => {
        vec![
            $(kremis_sdk::Signal::new($entity, $attr, $val)),*
        ]
    };
}
