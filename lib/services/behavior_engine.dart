import 'dart:math';
import '../domain/models.dart';

/// Engine for generating natural-looking commit patterns.
/// Uses behavior configuration to create realistic commit schedules.
class BehaviorEngine {
  final Random _random;

  BehaviorEngine({Random? random}) : _random = random ?? Random();

  /// Generate a full plan based on behavior configuration
  PlanSummary generatePlan(BehaviorConfig config, List<String> messagePool) {
    final days = <PlannedDay>[];
    final allDays = config.dateRange.allDays;
    final totalDays = allDays.length;

    for (var i = 0; i < allDays.length; i++) {
      final day = allDays[i];
      final isWeekend = day.weekday == DateTime.saturday || day.weekday == DateTime.sunday;
      final isHoliday = _isHoliday(day, config.holidays);

      // Calculate commit count for this day
      final count = _calculateDayCommitCount(
        day: day,
        dayIndex: i,
        totalDays: totalDays,
        config: config,
        isHoliday: isHoliday,
      );

      // Generate commits for this day
      final commits = _generateDayCommits(
        day: day,
        count: count,
        config: config,
        messagePool: messagePool,
      );

      days.add(PlannedDay(
        day: day,
        commits: commits,
        isHoliday: isHoliday,
        isWeekend: isWeekend,
      ));
    }

    return PlanSummary(days: days, config: config);
  }

  /// Calculate the number of commits for a specific day
  int _calculateDayCommitCount({
    required DateTime day,
    required int dayIndex,
    required int totalDays,
    required BehaviorConfig config,
    required bool isHoliday,
  }) {
    // Holidays get near-zero commits (occasionally 1)
    if (isHoliday) {
      return _random.nextDouble() < 0.1 ? 1 : 0;
    }

    // Base mean calculation
    double mean = config.averageIntensity;

    // Apply weekday weight
    final weekdayWeight = config.weekdayWeights[day.weekday] ?? 1.0;
    mean *= weekdayWeight;

    // Apply monthly trend (seasonal variation)
    final monthIndex = day.month - 1; // 0-11
    if (config.monthlyTrend.length > monthIndex) {
      mean *= config.monthlyTrend[monthIndex];
    }

    // Apply gradual trend slope (progress over time)
    if (totalDays > 1 && config.trendSlope != 0) {
      final progress = dayIndex / (totalDays - 1); // 0.0 to 1.0
      final trendMultiplier = 1.0 + (config.trendSlope * progress);
      mean *= trendMultiplier;
    }

    // Sample from distribution
    int count;
    switch (config.samplingMode) {
      case SamplingMode.poisson:
        count = _samplePoisson(mean);
        break;
      case SamplingMode.normal:
        count = _sampleNormal(mean, mean * 0.5).round(); // stddev = 50% of mean
        break;
    }

    // Apply jitter
    if (config.jitter > 0) {
      final jitterValue = _random.nextInt(config.jitter * 2 + 1) - config.jitter;
      count += jitterValue;
    }

    // Apply min/max caps
    count = count.clamp(config.minPerDay, config.maxPerDay);

    return count;
  }

  /// Generate commits for a day with intra-day scheduling
  List<PlannedCommit> _generateDayCommits({
    required DateTime day,
    required int count,
    required BehaviorConfig config,
    required List<String> messagePool,
  }) {
    if (count == 0) return [];

    final commits = <PlannedCommit>[];
    final intraDayConfig = config.intraDayConfig;

    for (var i = 0; i < count; i++) {
      final timestamp = _generateCommitTime(day, intraDayConfig);
      final message = _selectMessage(messagePool);

      commits.add(PlannedCommit(
        timestamp: timestamp,
        message: message,
      ));
    }

    // Sort commits by timestamp
    commits.sort((a, b) => a.timestamp.compareTo(b.timestamp));

    return commits;
  }

  /// Generate a commit timestamp for a day based on intra-day config
  DateTime _generateCommitTime(DateTime day, IntraDayConfig config) {
    // Check for late-night commit
    if (_random.nextDouble() < config.lateNightProbability) {
      return IntraDayConfig.lateNightWindow.randomTimeOn(day, _random.nextDouble());
    }

    // Select a work window weighted by duration
    final windows = config.workWindows;
    if (windows.isEmpty) {
      // Fallback: random time between 9am and 6pm
      return DateTime(day.year, day.month, day.day, 9 + _random.nextInt(9), _random.nextInt(60));
    }

    // Weight by window duration
    final totalDuration = windows.fold<int>(0, (sum, w) => sum + w.durationMinutes);
    var randomMinutes = _random.nextInt(totalDuration);

    for (final window in windows) {
      if (randomMinutes < window.durationMinutes) {
        final fraction = randomMinutes / window.durationMinutes;
        return window.randomTimeOn(day, fraction);
      }
      randomMinutes -= window.durationMinutes;
    }

    // Fallback to first window
    return windows.first.randomTimeOn(day, _random.nextDouble());
  }

  /// Select a random message from the pool
  String _selectMessage(List<String> pool) {
    if (pool.isEmpty) {
      return 'chore: update notes';
    }
    return pool[_random.nextInt(pool.length)];
  }

  /// Check if a day is a holiday
  bool _isHoliday(DateTime day, List<DateTime> holidays) {
    return holidays.any((h) =>
        h.year == day.year && h.month == day.month && h.day == day.day);
  }

  /// Sample from Poisson distribution
  int _samplePoisson(double lambda) {
    if (lambda <= 0) return 0;

    // For large lambda, use normal approximation
    if (lambda > 30) {
      return _sampleNormal(lambda, sqrt(lambda)).round().clamp(0, 100);
    }

    // Knuth algorithm for small lambda
    final l = exp(-lambda);
    var k = 0;
    var p = 1.0;

    do {
      k++;
      p *= _random.nextDouble();
    } while (p > l);

    return k - 1;
  }

  /// Sample from Normal distribution using Box-Muller transform
  double _sampleNormal(double mean, double stddev) {
    final u1 = _random.nextDouble();
    final u2 = _random.nextDouble();
    final z0 = sqrt(-2.0 * log(u1)) * cos(2.0 * pi * u2);
    return z0 * stddev + mean;
  }

  /// Blend user's GitHub contribution profile into behavior config
  BehaviorConfig blendWithProfile(
    BehaviorConfig config,
    ContributionProfile profile, {
    double profileWeight = 0.5,
  }) {
    final userWeight = profileWeight.clamp(0.0, 1.0);
    final configWeight = 1.0 - userWeight;

    // Blend average intensity
    final blendedIntensity = (config.averageIntensity * configWeight) +
        (profile.averageIntensity * userWeight);

    // Blend weekday weights
    final profileWeights = profile.weekdayWeights;
    final blendedWeights = <int, double>{};
    for (var day = 1; day <= 7; day++) {
      final configVal = config.weekdayWeights[day] ?? 1.0;
      final profileVal = profileWeights[day] ?? 1.0;
      blendedWeights[day] = (configVal * configWeight) + (profileVal * userWeight);
    }

    return config.copyWith(
      averageIntensity: blendedIntensity,
      weekdayWeights: blendedWeights,
    );
  }
}
