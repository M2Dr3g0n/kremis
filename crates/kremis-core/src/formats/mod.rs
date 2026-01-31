//! # Formats Module
//!
//! Serialization and format handling for Kremis graphs.
//!
//! MIGRATED FROM: kremis-facet-std (persistence, json_facet)
//!
//! This module contains:
//! - Binary persistence format (postcard + header)
//! - JSON serialization utilities
//!
//! Note: File I/O operations remain in the app layer (apps/kremis).
//! This module only handles format conversion (pure transformations).

mod persistence;

pub use persistence::*;
