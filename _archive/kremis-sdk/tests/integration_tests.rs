//! Integration tests for kremis-sdk.
//!
//! Uses wiremock to mock HTTP responses from the Kremis server.

// Allow unwrap and panic in tests - these are standard for test code
#![allow(clippy::unwrap_used, clippy::panic)]

use kremis_sdk::{
    Edge, Error, HealthResponse, IngestResponse, KremisClient, Query, QueryResponse, Signal,
    StageResponse, StatusResponse,
};
use wiremock::matchers::{method, path};
use wiremock::{Mock, MockServer, ResponseTemplate};

// =============================================================================
// SIGNAL TESTS
// =============================================================================

#[test]
fn test_signal_creation() {
    let signal = Signal::new(1, "temperature", "25.0");
    assert_eq!(signal.entity_id, 1);
    assert_eq!(signal.attribute, "temperature");
    assert_eq!(signal.value, "25.0");
}

#[test]
fn test_signal_with_string_types() {
    let signal = Signal::new(42, String::from("humidity"), String::from("60%"));
    assert_eq!(signal.entity_id, 42);
    assert_eq!(signal.attribute, "humidity");
    assert_eq!(signal.value, "60%");
}

#[test]
fn test_signal_serialization() {
    let signal = Signal::new(1, "attr", "val");
    let json = serde_json::to_string(&signal).unwrap();
    assert!(json.contains("\"entity_id\":1"));
    assert!(json.contains("\"attribute\":\"attr\""));
    assert!(json.contains("\"value\":\"val\""));
}

#[test]
fn test_signal_deserialization() {
    let json = r#"{"entity_id":5,"attribute":"test","value":"data"}"#;
    let signal: Signal = serde_json::from_str(json).unwrap();
    assert_eq!(signal.entity_id, 5);
    assert_eq!(signal.attribute, "test");
    assert_eq!(signal.value, "data");
}

// =============================================================================
// SIGNALS MACRO TESTS
// =============================================================================

#[test]
fn test_signals_macro_empty() {
    let signals: Vec<Signal> = kremis_sdk::signals![];
    assert!(signals.is_empty());
}

#[test]
fn test_signals_macro_single() {
    let signals = kremis_sdk::signals![(1, "a", "b")];
    assert_eq!(signals.len(), 1);
    assert_eq!(signals[0].entity_id, 1);
}

#[test]
fn test_signals_macro_multiple() {
    let signals = kremis_sdk::signals![
        (1, "temperature", "25.0"),
        (2, "humidity", "60%"),
        (3, "pressure", "1013hPa"),
    ];
    assert_eq!(signals.len(), 3);
    assert_eq!(signals[0].attribute, "temperature");
    assert_eq!(signals[1].attribute, "humidity");
    assert_eq!(signals[2].attribute, "pressure");
}

// =============================================================================
// RESPONSE TYPE TESTS
// =============================================================================

#[test]
fn test_health_response_deserialization() {
    let json = r#"{"status":"ok","version":"0.1.0"}"#;
    let resp: HealthResponse = serde_json::from_str(json).unwrap();
    assert_eq!(resp.status, "ok");
    assert_eq!(resp.version, "0.1.0");
}

#[test]
fn test_status_response_deserialization() {
    let json = r#"{"node_count":10,"edge_count":15,"stable_edges":5,"density_millionths":150000}"#;
    let resp: StatusResponse = serde_json::from_str(json).unwrap();
    assert_eq!(resp.node_count, 10);
    assert_eq!(resp.edge_count, 15);
    assert_eq!(resp.stable_edges, 5);
    assert_eq!(resp.density_millionths, 150000);
}

#[test]
fn test_stage_response_deserialization() {
    let json = r#"{"stage":"S1","name":"Pattern Crystallization","progress_percent":45,"stable_edges_needed":100,"stable_edges_current":45}"#;
    let resp: StageResponse = serde_json::from_str(json).unwrap();
    assert_eq!(resp.stage, "S1");
    assert_eq!(resp.name, "Pattern Crystallization");
    assert_eq!(resp.progress_percent, 45);
    assert_eq!(resp.stable_edges_needed, 100);
    assert_eq!(resp.stable_edges_current, 45);
}

#[test]
fn test_ingest_response_success() {
    let json = r#"{"success":true,"node_id":42,"error":null}"#;
    let resp: IngestResponse = serde_json::from_str(json).unwrap();
    assert!(resp.success);
    assert_eq!(resp.node_id, Some(42));
    assert!(resp.error.is_none());
}

#[test]
fn test_ingest_response_failure() {
    let json = r#"{"success":false,"node_id":null,"error":"Invalid signal"}"#;
    let resp: IngestResponse = serde_json::from_str(json).unwrap();
    assert!(!resp.success);
    assert!(resp.node_id.is_none());
    assert_eq!(resp.error, Some("Invalid signal".to_string()));
}

#[test]
fn test_query_response_found() {
    let json = r#"{"success":true,"found":true,"path":[1,2,3],"edges":[{"from":1,"to":2,"weight":10}],"error":null}"#;
    let resp: QueryResponse = serde_json::from_str(json).unwrap();
    assert!(resp.success);
    assert!(resp.found);
    assert_eq!(resp.path, vec![1, 2, 3]);
    assert_eq!(resp.edges.len(), 1);
    assert_eq!(resp.edges[0].from, 1);
    assert_eq!(resp.edges[0].to, 2);
    assert_eq!(resp.edges[0].weight, 10);
}

#[test]
fn test_query_response_not_found() {
    let json = r#"{"success":true,"found":false,"path":[],"edges":[],"error":null}"#;
    let resp: QueryResponse = serde_json::from_str(json).unwrap();
    assert!(resp.success);
    assert!(!resp.found);
    assert!(resp.path.is_empty());
    assert!(resp.edges.is_empty());
}

#[test]
fn test_edge_deserialization() {
    let json = r#"{"from":1,"to":2,"weight":100}"#;
    let edge: Edge = serde_json::from_str(json).unwrap();
    assert_eq!(edge.from, 1);
    assert_eq!(edge.to, 2);
    assert_eq!(edge.weight, 100);
}

// =============================================================================
// QUERY TYPE TESTS
// =============================================================================

#[test]
fn test_query_lookup_serialization() {
    let query = Query::Lookup { entity_id: 42 };
    let json = serde_json::to_string(&query).unwrap();
    assert!(json.contains("\"type\":\"lookup\""));
    assert!(json.contains("\"entity_id\":42"));
}

#[test]
fn test_query_traverse_serialization() {
    let query = Query::Traverse {
        node_id: 1,
        depth: 3,
    };
    let json = serde_json::to_string(&query).unwrap();
    assert!(json.contains("\"type\":\"traverse\""));
    assert!(json.contains("\"node_id\":1"));
    assert!(json.contains("\"depth\":3"));
}

#[test]
fn test_query_traverse_filtered_serialization() {
    let query = Query::TraverseFiltered {
        node_id: 1,
        depth: 2,
        min_weight: 50,
    };
    let json = serde_json::to_string(&query).unwrap();
    assert!(json.contains("\"type\":\"traverse_filtered\""));
    assert!(json.contains("\"min_weight\":50"));
}

#[test]
fn test_query_strongest_path_serialization() {
    let query = Query::StrongestPath { start: 1, end: 10 };
    let json = serde_json::to_string(&query).unwrap();
    assert!(json.contains("\"type\":\"strongest_path\""));
    assert!(json.contains("\"start\":1"));
    assert!(json.contains("\"end\":10"));
}

#[test]
fn test_query_intersect_serialization() {
    let query = Query::Intersect {
        nodes: vec![1, 2, 3],
    };
    let json = serde_json::to_string(&query).unwrap();
    assert!(json.contains("\"type\":\"intersect\""));
    assert!(json.contains("[1,2,3]"));
}

#[test]
fn test_query_related_serialization() {
    let query = Query::Related {
        node_id: 5,
        depth: 2,
    };
    let json = serde_json::to_string(&query).unwrap();
    assert!(json.contains("\"type\":\"related\""));
    assert!(json.contains("\"node_id\":5"));
}

// =============================================================================
// CLIENT TESTS WITH WIREMOCK
// =============================================================================

#[tokio::test]
async fn test_client_health() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/health"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "status": "ok",
            "version": "0.1.0"
        })))
        .mount(&mock_server)
        .await;

    let client = KremisClient::new(mock_server.uri());
    let health = client.health().await.unwrap();

    assert_eq!(health.status, "ok");
    assert_eq!(health.version, "0.1.0");
}

#[tokio::test]
async fn test_client_status() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/status"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "node_count": 100,
            "edge_count": 250,
            "stable_edges": 50,
            "density_millionths": 250000
        })))
        .mount(&mock_server)
        .await;

    let client = KremisClient::new(mock_server.uri());
    let status = client.status().await.unwrap();

    assert_eq!(status.node_count, 100);
    assert_eq!(status.edge_count, 250);
    assert_eq!(status.stable_edges, 50);
    assert_eq!(status.density_millionths, 250000);
}

#[tokio::test]
async fn test_client_stage() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/stage"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "stage": "S2",
            "name": "Signal-Response Emergence",
            "progress_percent": 75,
            "stable_edges_needed": 1000,
            "stable_edges_current": 750
        })))
        .mount(&mock_server)
        .await;

    let client = KremisClient::new(mock_server.uri());
    let stage = client.stage().await.unwrap();

    assert_eq!(stage.stage, "S2");
    assert_eq!(stage.name, "Signal-Response Emergence");
    assert_eq!(stage.progress_percent, 75);
}

#[tokio::test]
async fn test_client_ingest_success() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path("/signal"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "success": true,
            "node_id": 42,
            "error": null
        })))
        .mount(&mock_server)
        .await;

    let client = KremisClient::new(mock_server.uri());
    let signal = Signal::new(1, "test", "value");
    let result = client.ingest(&signal).await.unwrap();

    assert!(result.success);
    assert_eq!(result.node_id, Some(42));
}

#[tokio::test]
async fn test_client_ingest_error() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path("/signal"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "success": false,
            "node_id": null,
            "error": "Invalid entity_id"
        })))
        .mount(&mock_server)
        .await;

    let client = KremisClient::new(mock_server.uri());
    let signal = Signal::new(0, "test", "value");
    let result = client.ingest(&signal).await;

    assert!(result.is_err());
    match result.unwrap_err() {
        Error::Server(msg) => assert_eq!(msg, "Invalid entity_id"),
        _ => panic!("Expected Server error"),
    }
}

#[tokio::test]
async fn test_client_lookup_found() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path("/query"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "success": true,
            "found": true,
            "path": [42],
            "edges": [],
            "error": null
        })))
        .mount(&mock_server)
        .await;

    let client = KremisClient::new(mock_server.uri());
    let result = client.lookup(42).await.unwrap();

    assert_eq!(result, Some(42));
}

#[tokio::test]
async fn test_client_lookup_not_found() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path("/query"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "success": true,
            "found": false,
            "path": [],
            "edges": [],
            "error": null
        })))
        .mount(&mock_server)
        .await;

    let client = KremisClient::new(mock_server.uri());
    let result = client.lookup(999).await.unwrap();

    assert_eq!(result, None);
}

#[tokio::test]
async fn test_client_traverse() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path("/query"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "success": true,
            "found": true,
            "path": [1, 2, 3, 4],
            "edges": [
                {"from": 1, "to": 2, "weight": 10},
                {"from": 2, "to": 3, "weight": 15},
                {"from": 3, "to": 4, "weight": 20}
            ],
            "error": null
        })))
        .mount(&mock_server)
        .await;

    let client = KremisClient::new(mock_server.uri());
    let result = client.traverse(1, 3).await.unwrap();

    assert!(result.found);
    assert_eq!(result.path, vec![1, 2, 3, 4]);
    assert_eq!(result.edges.len(), 3);
}

#[tokio::test]
async fn test_client_strongest_path() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path("/query"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "success": true,
            "found": true,
            "path": [1, 5, 10],
            "edges": [
                {"from": 1, "to": 5, "weight": 100},
                {"from": 5, "to": 10, "weight": 100}
            ],
            "error": null
        })))
        .mount(&mock_server)
        .await;

    let client = KremisClient::new(mock_server.uri());
    let path = client.strongest_path(1, 10).await.unwrap();

    assert_eq!(path, vec![1, 5, 10]);
}

#[tokio::test]
async fn test_client_http_error() {
    let mock_server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path("/health"))
        .respond_with(ResponseTemplate::new(500))
        .mount(&mock_server)
        .await;

    let client = KremisClient::new(mock_server.uri());
    let result = client.health().await;

    // Should fail due to non-JSON response from 500 error
    assert!(result.is_err());
}

#[tokio::test]
async fn test_client_connection_refused() {
    // Use a port that's definitely not listening
    let client = KremisClient::new("http://127.0.0.1:1");
    let result = client.health().await;

    assert!(result.is_err());
    match result.unwrap_err() {
        Error::Http(_) => {} // Expected
        other => panic!("Expected Http error, got: {:?}", other),
    }
}

// =============================================================================
// ERROR TYPE TESTS
// =============================================================================

#[test]
fn test_error_display_server() {
    let err = Error::Server("test error".to_string());
    assert_eq!(format!("{}", err), "Server error: test error");
}

#[test]
fn test_error_display_json() {
    let json_err = serde_json::from_str::<Signal>("invalid").unwrap_err();
    let err = Error::Json(json_err);
    assert!(format!("{}", err).starts_with("JSON error:"));
}
