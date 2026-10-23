import time
import config

class TrafficController:
    """
    Adaptive Traffic Controller State Machine.
    Preserves exact traffic logic from traffic_demo_v3.py:
    - 1 vehicle = 5 seconds (Max 60s, Min 5s)
    - Yellow duration = 3 seconds
    - Skipping 0-vehicle directions when other traffic exists
    - +10 vehicle priority interruption rule
    - Resumes normal cycle after priority phase
    """
    def __init__(self):
        self.directions = config.DIRECTIONS
        self.current_index = 0
        self.current_direction = self.directions[0]
        self.current_state = "GREEN"
        
        self.phase_duration = config.MIN_GREEN
        self.phase_start = time.time()
        
        self.priority_active = False
        self.priority_direction = None
        self.priority_info = None
        self.last_priority_direction = None
        
        self.cycle_count = 1
        
        self.counts = {d: 0 for d in self.directions}
        self.green_times = {d: 0 for d in self.directions}

    def calculate_green_time(self, vehicle_count):
        """1 vehicle = 5 seconds, max 60s, 0 vehicles = 0s."""
        if vehicle_count <= 0:
            return 0
        green_time = vehicle_count * config.SECONDS_PER_VEHICLE
        return min(green_time, config.MAX_GREEN)

    def find_next_direction(self, current_index, counts):
        """Find next non-empty direction in cyclic order."""
        total = len(self.directions)
        for step in range(1, total + 1):
            index = (current_index + step) % total
            direction = self.directions[index]
            if counts[direction] > 0:
                return index
        return None

    def find_priority_direction(self, current_direction, counts):
        """Check if any direction has AT LEAST 10 MORE vehicles than active direction."""
        current_count = counts.get(current_direction, 0)
        best_direction = None
        best_difference = 0

        for direction in self.directions:
            if direction == current_direction:
                continue
            other_count = counts[direction]
            difference = other_count - current_count

            if difference >= config.PRIORITY_DIFFERENCE:
                if difference > best_difference:
                    best_difference = difference
                    best_direction = direction

        return best_direction, best_difference

    def update(self, new_counts):
        """
        Call on every frame update with latest vehicle counts.
        Updates state transitions, countdown timer, priority checks.
        """
        self.counts = new_counts

        # Update green time calculations for all approaches
        for d in self.directions:
            self.green_times[d] = self.calculate_green_time(self.counts[d])

        # Priority interruption check while GREEN phase
        if self.current_state == "GREEN" and not self.priority_active and self.current_direction:
            p_dir, p_diff = self.find_priority_direction(self.current_direction, self.counts)
            if p_dir is not None:
                self.priority_active = True
                self.priority_direction = p_dir
                self.priority_info = {
                    "priority_dir": p_dir,
                    "priority_count": self.counts[p_dir],
                    "current_dir": self.current_direction,
                    "current_count": self.counts[self.current_direction],
                    "diff": p_diff
                }

        # Timer calculations
        now = time.time()
        elapsed = now - self.phase_start
        remaining = max(0, int(self.phase_duration - elapsed))

        # Check phase completion
        if elapsed >= self.phase_duration:
            if self.current_state == "GREEN":
                # Transition GREEN -> YELLOW
                self.current_state = "YELLOW"
                self.phase_duration = config.YELLOW_TIME
                self.phase_start = now
            else:
                # Transition YELLOW -> NEXT GREEN
                if self.priority_active:
                    # Priority Interruption Triggered!
                    self.current_direction = self.priority_direction
                    self.current_index = self.directions.index(self.priority_direction)
                    self.current_state = "GREEN"
                    
                    calc_green = self.green_times[self.priority_direction]
                    self.phase_duration = max(config.MIN_GREEN, calc_green)
                    self.phase_start = now
                    
                    self.last_priority_direction = self.priority_direction
                    self.priority_active = False
                    self.priority_direction = None
                else:
                    # Normal Cycle
                    next_index = self.find_next_direction(self.current_index, self.counts)
                    if next_index is not None:
                        self.current_index = next_index
                        self.current_direction = self.directions[self.current_index]
                        self.current_state = "GREEN"
                        calc_green = self.green_times[self.current_direction]
                        self.phase_duration = max(config.MIN_GREEN, calc_green)
                        self.phase_start = now
                    else:
                        # All approaches empty: continue normal cycle with MIN_GREEN
                        self.current_index = (self.current_index + 1) % len(self.directions)
                        self.current_direction = self.directions[self.current_index]
                        self.current_state = "GREEN"
                        self.phase_duration = config.MIN_GREEN
                        self.phase_start = now
                    
                    # Track cycle loop
                    if self.current_index == 0:
                        self.cycle_count += 1

        return {
            "current_direction": self.current_direction,
            "current_state": self.current_state,
            "remaining_seconds": remaining,
            "phase_duration": self.phase_duration,
            "elapsed_seconds": int(elapsed),
            "priority_active": self.priority_active,
            "priority_direction": self.priority_direction,
            "priority_info": self.priority_info,
            "last_priority_direction": self.last_priority_direction,
            "cycle_count": self.cycle_count,
            "counts": self.counts,
            "green_times": self.green_times
        }
