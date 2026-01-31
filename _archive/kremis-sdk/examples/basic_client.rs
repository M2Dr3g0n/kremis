//! Basic Client Example
//!
//! This example demonstrates basic usage of the Kremis SDK client.
//!
//! Prerequisites:
//! - A Kremis server running on localhost:8080
//!
//! Run with:
//! ```sh
//! cargo run --example basic_client
//! ```

use kremis_sdk::{Error, KremisClient, Query, Signal};

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Create a client connecting to the local Kremis server
    let client = KremisClient::new("http://localhost:8080");

    println!("=== Kremis SDK Basic Client Example ===\n");

    // Step 1: Health check
    println!("1. Checking server health...");
    match client.health().await {
        Ok(health) => {
            println!("   Status: {}", health.status);
            println!("   Version: {}", health.version);
        }
        Err(e) => {
            eprintln!("   Failed to connect to server: {}", e);
            eprintln!("   Make sure the Kremis server is running on localhost:8080");
            return Err(e);
        }
    }

    // Step 2: Check graph status
    println!("\n2. Getting graph status...");
    let status = client.status().await?;
    println!("   Node count: {}", status.node_count);
    println!("   Edge count: {}", status.edge_count);
    println!("   Stable edges: {}", status.stable_edges);
    println!("   Density (millionths): {}", status.density_millionths);

    // Step 3: Check developmental stage
    println!("\n3. Checking developmental stage...");
    let stage = client.stage().await?;
    println!("   Stage: {} ({})", stage.stage, stage.name);
    println!("   Progress: {}%", stage.progress_percent);
    println!(
        "   Stable edges: {}/{}",
        stage.stable_edges_current, stage.stable_edges_needed
    );

    // Step 4: Ingest a single signal
    println!("\n4. Ingesting a signal...");
    let signal = Signal::new(1001, "sensor_type", "temperature");
    let result = client.ingest(&signal).await?;
    println!("   Success: {}", result.success);
    if let Some(node_id) = result.node_id {
        println!("   Node ID: {}", node_id);
    }

    // Step 5: Ingest more signals to build relationships
    println!("\n5. Ingesting additional signals...");
    let signals = vec![
        Signal::new(1001, "value", "25.5"),
        Signal::new(1001, "unit", "celsius"),
        Signal::new(1002, "sensor_type", "humidity"),
        Signal::new(1002, "value", "60"),
        Signal::new(1002, "unit", "percent"),
    ];

    for signal in &signals {
        let result = client.ingest(signal).await?;
        println!(
            "   Ingested entity {} attribute '{}': node {:?}",
            signal.entity_id, signal.attribute, result.node_id
        );
    }

    // Step 6: Query - Lookup an entity
    println!("\n6. Looking up entity 1001...");
    if let Some(node_id) = client.lookup(1001).await? {
        println!("   Found at node: {}", node_id);

        // Step 7: Traverse from the found node
        println!("\n7. Traversing from node {} (depth=2)...", node_id);
        let traverse_result = client.traverse(node_id, 2).await?;
        println!("   Found {} edges:", traverse_result.edges.len());
        for edge in &traverse_result.edges {
            println!(
                "      {} -> {} (weight: {})",
                edge.from, edge.to, edge.weight
            );
        }
    } else {
        println!("   Entity 1001 not found in graph");
    }

    // Step 8: Query - Find strongest path (if we have two known nodes)
    println!("\n8. Finding strongest path between entities...");
    let node_a = client.lookup(1001).await?;
    let node_b = client.lookup(1002).await?;

    if let (Some(a), Some(b)) = (node_a, node_b) {
        let path = client.strongest_path(a, b).await?;
        if path.is_empty() {
            println!("   No path found between nodes {} and {}", a, b);
        } else {
            println!("   Path: {:?}", path);
        }
    } else {
        println!("   Could not find both entities for path query");
    }

    // Step 9: Advanced query - Related nodes
    println!("\n9. Querying related nodes...");
    if let Some(node_id) = client.lookup(1001).await? {
        let query = Query::Related { node_id, depth: 3 };
        let result = client.query(&query).await?;
        println!("   Found {} related nodes", result.path.len());
        if !result.path.is_empty() {
            println!("   Nodes: {:?}", result.path);
        }
    }

    // Step 10: Final status check
    println!("\n10. Final graph status...");
    let final_status = client.status().await?;
    println!("    Node count: {}", final_status.node_count);
    println!("    Edge count: {}", final_status.edge_count);

    println!("\n=== Example completed successfully ===");
    Ok(())
}
