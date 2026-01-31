//! Batch Signals Example
//!
//! This example demonstrates batch ingestion using the `signals!` macro
//! for efficiently creating and ingesting multiple signals.
//!
//! Prerequisites:
//! - A Kremis server running on localhost:8080
//!
//! Run with:
//! ```sh
//! cargo run --example batch_signals
//! ```

use kremis_sdk::{signals, Error, KremisClient, Signal};

#[tokio::main]
async fn main() -> Result<(), Error> {
    let client = KremisClient::new("http://localhost:8080");

    println!("=== Kremis SDK Batch Signals Example ===\n");

    // Check server is available
    println!("Connecting to server...");
    match client.health().await {
        Ok(health) => println!("Connected to Kremis v{}\n", health.version),
        Err(e) => {
            eprintln!("Failed to connect: {}", e);
            eprintln!("Make sure the Kremis server is running on localhost:8080");
            return Err(e);
        }
    }

    // Get initial status
    let initial_status = client.status().await?;
    println!(
        "Initial graph: {} nodes, {} edges\n",
        initial_status.node_count, initial_status.edge_count
    );

    // =========================================================================
    // Example 1: Using the signals! macro for concise signal creation
    // =========================================================================
    println!("--- Example 1: Using signals! macro ---\n");

    // The signals! macro creates a Vec<Signal> from a list of tuples
    let weather_signals = signals![
        (100, "type", "weather_station"),
        (100, "location", "Rome"),
        (100, "latitude", "41.9028"),
        (100, "longitude", "12.4964"),
        (101, "type", "temperature_reading"),
        (101, "station_id", "100"),
        (101, "value", "22.5"),
        (101, "unit", "celsius"),
        (101, "timestamp", "2026-01-22T10:00:00Z"),
        (102, "type", "humidity_reading"),
        (102, "station_id", "100"),
        (102, "value", "65"),
        (102, "unit", "percent"),
        (102, "timestamp", "2026-01-22T10:00:00Z"),
    ];

    println!(
        "Created {} signals using signals! macro",
        weather_signals.len()
    );

    // Ingest all signals
    let mut success_count = 0;
    for signal in &weather_signals {
        match client.ingest(signal).await {
            Ok(result) if result.success => {
                success_count += 1;
            }
            Ok(result) => {
                eprintln!(
                    "Warning: Signal rejected: {:?}",
                    result.error.unwrap_or_default()
                );
            }
            Err(e) => {
                eprintln!("Error ingesting signal: {}", e);
            }
        }
    }
    println!(
        "Ingested {}/{} signals\n",
        success_count,
        weather_signals.len()
    );

    // =========================================================================
    // Example 2: Building signals programmatically for batch operations
    // =========================================================================
    println!("--- Example 2: Programmatic batch creation ---\n");

    // Simulate sensor data from multiple sensors
    let sensor_ids: Vec<u64> = (200..205).collect();
    let sensor_types = ["temperature", "humidity", "pressure", "light", "motion"];

    let mut sensor_signals: Vec<Signal> = Vec::new();

    for (idx, &sensor_id) in sensor_ids.iter().enumerate() {
        // Each sensor gets multiple attributes
        sensor_signals.push(Signal::new(sensor_id, "type", "sensor"));
        sensor_signals.push(Signal::new(sensor_id, "sensor_type", sensor_types[idx]));
        sensor_signals.push(Signal::new(
            sensor_id,
            "location",
            format!("zone_{}", idx + 1),
        ));
        sensor_signals.push(Signal::new(sensor_id, "active", "true"));
    }

    println!(
        "Created {} signals for {} sensors",
        sensor_signals.len(),
        sensor_ids.len()
    );

    // Batch ingest with progress tracking
    let total = sensor_signals.len();
    let mut ingested = 0;

    for (idx, signal) in sensor_signals.iter().enumerate() {
        if client.ingest(signal).await.is_ok() {
            ingested += 1;
        }

        // Progress indicator every 5 signals
        if (idx + 1) % 5 == 0 {
            println!("  Progress: {}/{}", idx + 1, total);
        }
    }
    println!("Completed: {}/{} signals ingested\n", ingested, total);

    // =========================================================================
    // Example 3: Creating relationship signals
    // =========================================================================
    println!("--- Example 3: Relationship signals ---\n");

    // Create entities and their relationships
    let relationship_signals = signals![
        // Define a user
        (300, "type", "user"),
        (300, "name", "Alice"),
        (300, "email", "alice@example.com"),
        // Define a project
        (301, "type", "project"),
        (301, "name", "Kremis Integration"),
        (301, "status", "active"),
        // Define a task
        (302, "type", "task"),
        (302, "title", "Implement SDK examples"),
        (302, "priority", "high"),
        // Relationships (using entity references)
        (300, "owns_project", "301"),
        (301, "has_task", "302"),
        (302, "assigned_to", "300"),
    ];

    println!(
        "Creating {} signals with relationships...",
        relationship_signals.len()
    );

    for signal in &relationship_signals {
        let result = client.ingest(signal).await?;
        if result.success {
            println!(
                "  [{}] {} = {} -> node {:?}",
                signal.entity_id, signal.attribute, signal.value, result.node_id
            );
        }
    }

    // =========================================================================
    // Final Summary
    // =========================================================================
    println!("\n--- Final Summary ---\n");

    let final_status = client.status().await?;
    let stage = client.stage().await?;

    println!("Graph Statistics:");
    println!(
        "  Nodes: {} (+{})",
        final_status.node_count,
        final_status
            .node_count
            .saturating_sub(initial_status.node_count)
    );
    println!(
        "  Edges: {} (+{})",
        final_status.edge_count,
        final_status
            .edge_count
            .saturating_sub(initial_status.edge_count)
    );
    println!("  Stable edges: {}", final_status.stable_edges);
    println!("\nDevelopmental Stage:");
    println!("  Stage: {} ({})", stage.stage, stage.name);
    println!("  Progress: {}%", stage.progress_percent);

    println!("\n=== Batch signals example completed ===");
    Ok(())
}
