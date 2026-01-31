//! # Active Context LRU Cache
//!
//! Per ROADMAP.md Section 1.3: Scalability & Caching
//!
//! This module implements an LRU (Least Recently Used) cache for "hot nodes"
//! to improve traversal performance on large graphs.
//!
//! ## Design Principles
//!
//! Per AGENTS.md:
//! - All data structures use BTreeMap for deterministic ordering
//! - No floating-point arithmetic
//! - Integer-only timestamps (logical clock, not wall clock)
//!
//! ## Integration
//!
//! The cache is integrated with the Session's Buffer (Active Context).

use crate::NodeId;
use std::collections::BTreeMap;

// =============================================================================
// LRU CACHE CONFIGURATION
// =============================================================================

/// Default maximum cache size.
pub const DEFAULT_CACHE_SIZE: usize = 1000;

/// Default eviction batch size (number of entries to evict at once).
pub const DEFAULT_EVICTION_BATCH: usize = 100;

// =============================================================================
// CACHE ENTRY
// =============================================================================

/// An entry in the LRU cache.
#[derive(Debug, Clone)]
pub struct CacheEntry<T> {
    /// The cached value.
    pub value: T,

    /// Logical timestamp of last access (for LRU ordering).
    /// Uses integer counter, not wall clock, for determinism.
    pub last_access: u64,

    /// Access count for statistics.
    pub access_count: u64,
}

impl<T> CacheEntry<T> {
    /// Create a new cache entry.
    fn new(value: T, timestamp: u64) -> Self {
        Self {
            value,
            last_access: timestamp,
            access_count: 1,
        }
    }

    /// Update the access timestamp.
    fn touch(&mut self, timestamp: u64) {
        self.last_access = timestamp;
        self.access_count = self.access_count.saturating_add(1);
    }
}

// =============================================================================
// LRU CACHE
// =============================================================================

/// LRU Cache for hot nodes.
///
/// Uses BTreeMap for deterministic ordering (per AGENTS.md Section 5.3).
/// The cache uses a logical clock (monotonic counter) instead of wall time
/// to ensure deterministic behavior.
#[derive(Debug)]
pub struct LruCache<K: Ord + Clone, V: Clone> {
    /// Cache storage: key -> entry.
    entries: BTreeMap<K, CacheEntry<V>>,

    /// Maximum cache size.
    max_size: usize,

    /// Eviction batch size.
    eviction_batch: usize,

    /// Logical clock for timestamps (monotonic counter).
    logical_clock: u64,

    /// Statistics: total hits.
    hits: u64,

    /// Statistics: total misses.
    misses: u64,
}

impl<K: Ord + Clone, V: Clone> Default for LruCache<K, V> {
    fn default() -> Self {
        Self::new(DEFAULT_CACHE_SIZE)
    }
}

impl<K: Ord + Clone, V: Clone> LruCache<K, V> {
    /// Create a new LRU cache with the given maximum size.
    #[must_use]
    pub fn new(max_size: usize) -> Self {
        Self {
            entries: BTreeMap::new(),
            max_size: max_size.max(1), // At least 1
            eviction_batch: DEFAULT_EVICTION_BATCH,
            logical_clock: 0,
            hits: 0,
            misses: 0,
        }
    }

    /// Create with custom eviction batch size.
    #[must_use]
    pub fn with_eviction_batch(mut self, batch_size: usize) -> Self {
        self.eviction_batch = batch_size.max(1);
        self
    }

    /// Get a value from the cache.
    ///
    /// Returns `Some(&V)` if found, `None` otherwise.
    /// Updates the access timestamp on hit.
    pub fn get(&mut self, key: &K) -> Option<&V> {
        self.logical_clock = self.logical_clock.saturating_add(1);
        let timestamp = self.logical_clock;

        if let Some(entry) = self.entries.get_mut(key) {
            entry.touch(timestamp);
            self.hits = self.hits.saturating_add(1);
            Some(&entry.value)
        } else {
            self.misses = self.misses.saturating_add(1);
            None
        }
    }

    /// Get a value without updating the access timestamp.
    ///
    /// Useful for read-only inspection.
    #[must_use]
    pub fn peek(&self, key: &K) -> Option<&V> {
        self.entries.get(key).map(|e| &e.value)
    }

    /// Insert a value into the cache.
    ///
    /// If the cache is full, evicts least recently used entries.
    pub fn insert(&mut self, key: K, value: V) {
        self.logical_clock = self.logical_clock.saturating_add(1);
        let timestamp = self.logical_clock;

        // Evict if necessary
        if self.entries.len() >= self.max_size && !self.entries.contains_key(&key) {
            self.evict();
        }

        // Insert or update
        if let Some(entry) = self.entries.get_mut(&key) {
            entry.value = value;
            entry.touch(timestamp);
        } else {
            self.entries.insert(key, CacheEntry::new(value, timestamp));
        }
    }

    /// Remove a specific key from the cache.
    pub fn remove(&mut self, key: &K) -> Option<V> {
        self.entries.remove(key).map(|e| e.value)
    }

    /// Clear the entire cache.
    pub fn clear(&mut self) {
        self.entries.clear();
        // Don't reset logical clock or stats
    }

    /// Get the current size of the cache.
    #[must_use]
    pub fn len(&self) -> usize {
        self.entries.len()
    }

    /// Check if the cache is empty.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Get cache statistics.
    #[must_use]
    pub fn stats(&self) -> CacheStats {
        CacheStats {
            size: self.entries.len(),
            max_size: self.max_size,
            hits: self.hits,
            misses: self.misses,
            hit_rate_percent: self.hit_rate_percent(),
        }
    }

    /// Calculate hit rate as integer percentage (0-100).
    #[must_use]
    pub fn hit_rate_percent(&self) -> u8 {
        let total = self.hits.saturating_add(self.misses);
        if total == 0 {
            0
        } else {
            ((self.hits.saturating_mul(100)) / total) as u8
        }
    }

    /// Evict least recently used entries.
    fn evict(&mut self) {
        if self.entries.is_empty() {
            return;
        }

        let to_evict = self.eviction_batch.min(self.entries.len());

        // Find entries with lowest last_access (LRU)
        // Using BTreeMap for determinism
        let mut by_access: BTreeMap<u64, Vec<K>> = BTreeMap::new();

        for (key, entry) in &self.entries {
            by_access
                .entry(entry.last_access)
                .or_default()
                .push(key.clone());
        }

        // Evict from oldest to newest
        let mut evicted = 0;
        'outer: for (_access_time, keys) in by_access {
            for key in keys {
                self.entries.remove(&key);
                evicted += 1;
                if evicted >= to_evict {
                    break 'outer;
                }
            }
        }
    }

    /// Check if a key exists in the cache.
    #[must_use]
    pub fn contains(&self, key: &K) -> bool {
        self.entries.contains_key(key)
    }

    /// Get all keys in the cache (deterministic order).
    pub fn keys(&self) -> impl Iterator<Item = &K> {
        self.entries.keys()
    }
}

// =============================================================================
// CACHE STATISTICS
// =============================================================================

/// Statistics about cache performance.
#[derive(Debug, Clone, Copy)]
pub struct CacheStats {
    /// Current number of entries.
    pub size: usize,

    /// Maximum cache size.
    pub max_size: usize,

    /// Total cache hits.
    pub hits: u64,

    /// Total cache misses.
    pub misses: u64,

    /// Hit rate as integer percentage (0-100).
    pub hit_rate_percent: u8,
}

// =============================================================================
// NODE CACHE (Specialized for NodeId)
// =============================================================================

/// Specialized LRU cache for hot nodes.
///
/// This is the primary cache type for the Active Context optimization.
pub type NodeCache<V> = LruCache<NodeId, V>;

/// Create a new node cache with default settings.
///
/// Returns a cache with `DEFAULT_CACHE_SIZE` (1000) entries.
/// This is suitable for most use cases with moderate-sized graphs.
///
/// # Example
///
/// ```ignore
/// use kremis_core::cache::node_cache;
///
/// let mut cache = node_cache::<String>();
/// ```
#[must_use]
pub fn node_cache<V: Clone>() -> NodeCache<V> {
    LruCache::new(DEFAULT_CACHE_SIZE)
}

/// Create a new node cache with custom size.
///
/// Use this when you need to control memory usage or have
/// specific cache size requirements.
///
/// # Arguments
///
/// * `size` - Maximum number of entries in the cache.
///
/// # Example
///
/// ```ignore
/// use kremis_core::cache::node_cache_with_size;
///
/// // Small cache for memory-constrained environments
/// let mut cache = node_cache_with_size::<String>(100);
/// ```
#[must_use]
pub fn node_cache_with_size<V: Clone>(size: usize) -> NodeCache<V> {
    LruCache::new(size)
}

// =============================================================================
// TRAVERSAL CACHE
// =============================================================================

/// Cache for traversal results.
///
/// Stores the result of expensive traversal operations
/// to avoid recomputation.
#[derive(Debug, Clone)]
pub struct TraversalCacheKey {
    /// Start node for the traversal.
    pub start: NodeId,

    /// Depth of the traversal.
    pub depth: usize,

    /// Minimum weight filter (optional).
    pub min_weight: Option<i64>,
}

impl TraversalCacheKey {
    /// Create a new traversal cache key.
    #[must_use]
    pub fn new(start: NodeId, depth: usize) -> Self {
        Self {
            start,
            depth,
            min_weight: None,
        }
    }

    /// Create with weight filter.
    #[must_use]
    pub fn with_filter(start: NodeId, depth: usize, min_weight: i64) -> Self {
        Self {
            start,
            depth,
            min_weight: Some(min_weight),
        }
    }
}

// Implement Ord for BTreeMap compatibility
impl Ord for TraversalCacheKey {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        (&self.start, self.depth, self.min_weight).cmp(&(
            &other.start,
            other.depth,
            other.min_weight,
        ))
    }
}

impl PartialOrd for TraversalCacheKey {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Eq for TraversalCacheKey {}

impl PartialEq for TraversalCacheKey {
    fn eq(&self, other: &Self) -> bool {
        self.start == other.start
            && self.depth == other.depth
            && self.min_weight == other.min_weight
    }
}

/// Cache for traversal results.
pub type TraversalCache = LruCache<TraversalCacheKey, crate::Artifact>;

/// Create a new traversal cache.
///
/// Returns a cache with 100 entries (smaller than node cache since
/// traversal results are larger in memory).
///
/// Use this to cache expensive traversal operations and avoid
/// recomputation when the same traversal is requested multiple times.
///
/// # Example
///
/// ```ignore
/// use kremis_core::cache::traversal_cache;
///
/// let mut cache = traversal_cache();
/// ```
#[must_use]
pub fn traversal_cache() -> TraversalCache {
    LruCache::new(100) // Smaller default for traversals (larger values)
}

// =============================================================================
// TESTS
// =============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cache_insert_and_get() {
        let mut cache = LruCache::new(10);
        cache.insert(1u64, "value1");
        cache.insert(2u64, "value2");

        assert_eq!(cache.get(&1), Some(&"value1"));
        assert_eq!(cache.get(&2), Some(&"value2"));
        assert_eq!(cache.get(&3), None);
    }

    #[test]
    fn cache_eviction() {
        let mut cache = LruCache::new(3).with_eviction_batch(1);

        cache.insert(1u64, "a");
        cache.insert(2u64, "b");
        cache.insert(3u64, "c");

        // Access 1 and 2 to make 3 the LRU
        let _ = cache.get(&1);
        let _ = cache.get(&2);

        // Insert 4, should evict 3 (LRU)
        cache.insert(4u64, "d");

        assert!(cache.contains(&1));
        assert!(cache.contains(&2));
        assert!(!cache.contains(&3)); // Evicted
        assert!(cache.contains(&4));
    }

    #[test]
    fn cache_stats() {
        let mut cache = LruCache::<u64, &str>::new(10);

        cache.insert(1, "a");
        let _ = cache.get(&1); // Hit
        let _ = cache.get(&2); // Miss
        let _ = cache.get(&1); // Hit
        let _ = cache.get(&3); // Miss

        let stats = cache.stats();
        assert_eq!(stats.hits, 2);
        assert_eq!(stats.misses, 2);
        assert_eq!(stats.hit_rate_percent, 50);
    }

    #[test]
    fn cache_peek_does_not_update() {
        let mut cache = LruCache::new(10);
        cache.insert(1u64, "value");

        let initial_stats = cache.stats();

        // Peek should not affect stats
        let _ = cache.peek(&1);
        let _ = cache.peek(&2);

        let after_stats = cache.stats();
        assert_eq!(initial_stats.hits, after_stats.hits);
        assert_eq!(initial_stats.misses, after_stats.misses);
    }

    #[test]
    fn cache_remove() {
        let mut cache = LruCache::new(10);
        cache.insert(1u64, "value");

        assert!(cache.contains(&1));
        let removed = cache.remove(&1);
        assert_eq!(removed, Some("value"));
        assert!(!cache.contains(&1));
    }

    #[test]
    fn cache_clear() {
        let mut cache = LruCache::new(10);
        cache.insert(1u64, "a");
        cache.insert(2u64, "b");

        cache.clear();
        assert!(cache.is_empty());
        assert_eq!(cache.len(), 0);
    }

    #[test]
    fn node_cache_creation() {
        let mut cache: NodeCache<String> = node_cache();
        cache.insert(NodeId(1), "test".to_string());
        assert_eq!(cache.get(&NodeId(1)), Some(&"test".to_string()));
    }

    #[test]
    fn traversal_cache_key_ordering() {
        let key1 = TraversalCacheKey::new(NodeId(1), 5);
        let key2 = TraversalCacheKey::new(NodeId(2), 5);
        let key3 = TraversalCacheKey::new(NodeId(1), 10);

        // Ordering is deterministic
        assert!(key1 < key2);
        assert!(key1 < key3);
    }

    #[test]
    fn cache_update_existing() {
        let mut cache = LruCache::new(10);
        cache.insert(1u64, "old");
        cache.insert(1u64, "new");

        assert_eq!(cache.get(&1), Some(&"new"));
        assert_eq!(cache.len(), 1);
    }

    #[test]
    fn deterministic_iteration() {
        let mut cache = LruCache::new(10);

        // Insert in arbitrary order
        cache.insert(5u64, "e");
        cache.insert(1u64, "a");
        cache.insert(3u64, "c");

        // Keys should be in sorted order (BTreeMap)
        let keys: Vec<_> = cache.keys().copied().collect();
        assert_eq!(keys, vec![1, 3, 5]);
    }
}
