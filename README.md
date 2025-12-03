# cache-architecture-simulator

DRAFT SCRIPT

Welcome to our cache memory simulator demo. We built this tool to let users explore how different cache configurations behave, visualize cache block contents, and test both random and locality-based access patterns.

First, we start by configuring the cache. The program asks for the nominal size in bytes, the number of words per block, the mapping policy, and—if set associative is chosen—the number of blocks per set. Once we enter these parameters and click configure, the simulator calculates and displays all the derived values: the number of blocks, the number of sets, the tag, index, and offset bit lengths, and the real cache size once tag and valid bits are included.

Below that is the cache visualization section. Each set is displayed with its ways, showing whether each block is valid, its tag, and the current LRU counter. Colors help identify invalid blocks, valid blocks, recent hits, and recent misses.

Next, we can manually access memory by entering a word address. When we type an address and press Access, the simulator determines the offset, index, and tag fields, checks the appropriate set, and shows whether the access was a hit or miss. It updates the LRU replacement policy automatically and highlights the accessed block in the visualization. The hit count, miss count, and hit-rate percentage are updated live. Every access—whether manual or simulated—is logged in a history window that shows timestamp, address, tag, index, offset, set, way, and hit or miss.

There’s also an option to clear the cache, which resets all valid bits, tags, LRU counters, and statistics.

For simulation mode, we can enter how many accesses we want. The Random option generates uniformly random addresses, while the Locality mode simulates more realistic behavior: most accesses cluster around a small working set, with occasional jumps to new regions. After the simulation completes, the tool updates the visualization and shows the resulting hit and miss rates.

This program supports multiple cache organizations. For the demo, we show four configurations:

First, direct mapped with one word per block. Here, the offset is zero bits, each address maps to exactly one block, and we can clearly see how conflict misses occur.

Second, direct mapped with multiple words per block. Now the offset bits increase, and spatial locality improves the chances of hits.

Third, set associative with one word per block. Because there are multiple ways per set, conflict misses are less severe, and LRU replacement becomes important.

Fourth, set associative with multiple words per block. This shows the full behavior of tag, index, offset, and LRU working together.

Throughout the video, we demonstrate manual accesses, show hits and misses, run random simulations, and run locality-based simulations so the improved hit rates are clear.

In building this program, we structured the cache as a list of sets, and each set contains its ways as small dictionaries storing the valid bit, tag, data words, and an LRU counter. Every access updates the LRU counters and replaces the least recently used block when needed. The address decoding and bit-field extraction are calculated based on the number of sets and words per block. The graphical interface is built with Tkinter, and all cache changes are immediately reflected visually.

That concludes the demonstration. This simulator supports all required features: manual configuration, address partitioning, hit and miss reporting, a persistent access log, cache clearing, random and locality-based simulations, graphical visualization, and LRU replacement. We’ve also shown it running in four required cache configurations.
