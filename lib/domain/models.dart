import 'package:collection/collection.dart';

// ============================================================================
// ENUMS
// ============================================================================

enum SamplingMode { poisson, normal }

enum HolidayRegion { vietnam, usa, japan, korea, eu }

enum RunStatus { pending, running, completed, failed, undone }

// ============================================================================
// TIME & DATE MODELS
// ============================================================================

class DateRange {
  final DateTime start;
  final DateTime end;
  const DateRange(this.start, this.end);

  int get dayCount => end.difference(start).inDays + 1;

  List<DateTime> get allDays {
    final days = <DateTime>[];
    var current = start;
    while (!current.isAfter(end)) {
      days.add(DateTime(current.year, current.month, current.day));
      current = current.add(const Duration(days: 1));
    }
    return days;
  }

  bool contains(DateTime date) {
    final d = DateTime(date.year, date.month, date.day);
    return !d.isBefore(start) && !d.isAfter(end);
  }

  Map<String, dynamic> toJson() => {
        'start': start.toIso8601String(),
        'end': end.toIso8601String(),
      };

  factory DateRange.fromJson(Map<String, dynamic> json) => DateRange(
        DateTime.parse(json['start'] as String),
        DateTime.parse(json['end'] as String),
      );
}

/// Represents a time window during a day (e.g., 09:30-12:00)
class TimeWindow {
  final int startHour;
  final int startMinute;
  final int endHour;
  final int endMinute;

  const TimeWindow({
    required this.startHour,
    required this.startMinute,
    required this.endHour,
    required this.endMinute,
  });

  int get startMinutes => startHour * 60 + startMinute;
  int get endMinutes => endHour * 60 + endMinute;
  int get durationMinutes => endMinutes - startMinutes;

  /// Generate a random time within this window
  DateTime randomTimeOn(DateTime day, double random01) {
    final minuteOffset = (random01 * durationMinutes).floor();
    final totalMinutes = startMinutes + minuteOffset;
    return DateTime(
      day.year,
      day.month,
      day.day,
      totalMinutes ~/ 60,
      totalMinutes % 60,
      (random01 * 60).floor(), // random seconds
    );
  }

  Map<String, dynamic> toJson() => {
        'startHour': startHour,
        'startMinute': startMinute,
        'endHour': endHour,
        'endMinute': endMinute,
      };

  factory TimeWindow.fromJson(Map<String, dynamic> json) => TimeWindow(
        startHour: json['startHour'] as int,
        startMinute: json['startMinute'] as int,
        endHour: json['endHour'] as int,
        endMinute: json['endMinute'] as int,
      );

  @override
  String toString() =>
      '${startHour.toString().padLeft(2, '0')}:${startMinute.toString().padLeft(2, '0')}-'
      '${endHour.toString().padLeft(2, '0')}:${endMinute.toString().padLeft(2, '0')}';
}

// ============================================================================
// IDENTITY CONFIG
// ============================================================================

class IdentityConfig {
  final String username;
  final String email;
  final String timezone;
  final String? githubPat; // Optional PAT for GraphQL fetch

  const IdentityConfig({
    required this.username,
    required this.email,
    required this.timezone,
    this.githubPat,
  });

  IdentityConfig copyWith({
    String? username,
    String? email,
    String? timezone,
    String? githubPat,
  }) =>
      IdentityConfig(
        username: username ?? this.username,
        email: email ?? this.email,
        timezone: timezone ?? this.timezone,
        githubPat: githubPat ?? this.githubPat,
      );

  Map<String, dynamic> toJson() => {
        'username': username,
        'email': email,
        'timezone': timezone,
        // PAT is not serialized for security
      };

  factory IdentityConfig.fromJson(Map<String, dynamic> json) => IdentityConfig(
        username: json['username'] as String,
        email: json['email'] as String,
        timezone: json['timezone'] as String,
      );

  static const empty = IdentityConfig(
    username: '',
    email: '',
    timezone: 'Asia/Ho_Chi_Minh',
  );
}

// ============================================================================
// REPO CONFIG
// ============================================================================

class RepoConfig {
  final String path;
  final String branch;
  final bool isValid;
  final String? gitVersion;
  final bool isDirty;
  final String? remoteUrl;

  const RepoConfig({
    required this.path,
    required this.branch,
    required this.isValid,
    this.gitVersion,
    this.isDirty = false,
    this.remoteUrl,
  });

  RepoConfig copyWith({
    String? path,
    String? branch,
    bool? isValid,
    String? gitVersion,
    bool? isDirty,
    String? remoteUrl,
  }) =>
      RepoConfig(
        path: path ?? this.path,
        branch: branch ?? this.branch,
        isValid: isValid ?? this.isValid,
        gitVersion: gitVersion ?? this.gitVersion,
        isDirty: isDirty ?? this.isDirty,
        remoteUrl: remoteUrl ?? this.remoteUrl,
      );

  Map<String, dynamic> toJson() => {
        'path': path,
        'branch': branch,
        'isValid': isValid,
        'gitVersion': gitVersion,
        'isDirty': isDirty,
        'remoteUrl': remoteUrl,
      };

  factory RepoConfig.fromJson(Map<String, dynamic> json) => RepoConfig(
        path: json['path'] as String,
        branch: json['branch'] as String,
        isValid: json['isValid'] as bool,
        gitVersion: json['gitVersion'] as String?,
        isDirty: json['isDirty'] as bool? ?? false,
        remoteUrl: json['remoteUrl'] as String?,
      );

  static const empty = RepoConfig(
    path: '',
    branch: '',
    isValid: false,
  );
}

// ============================================================================
// INTRA-DAY SCHEDULE CONFIG
// ============================================================================

class IntraDayConfig {
  final List<TimeWindow> workWindows;
  final bool hasLunchGap;
  final double lateNightProbability; // <5% for realism

  const IntraDayConfig({
    required this.workWindows,
    this.hasLunchGap = true,
    this.lateNightProbability = 0.03,
  });

  static const defaultConfig = IntraDayConfig(
    workWindows: [
      TimeWindow(startHour: 9, startMinute: 30, endHour: 12, endMinute: 0),
      TimeWindow(startHour: 13, startMinute: 30, endHour: 18, endMinute: 30),
    ],
    hasLunchGap: true,
    lateNightProbability: 0.03,
  );

  /// Late night window for occasional commits
  static const lateNightWindow = TimeWindow(
    startHour: 22,
    startMinute: 0,
    endHour: 23,
    endMinute: 59,
  );

  Map<String, dynamic> toJson() => {
        'workWindows': workWindows.map((w) => w.toJson()).toList(),
        'hasLunchGap': hasLunchGap,
        'lateNightProbability': lateNightProbability,
      };

  factory IntraDayConfig.fromJson(Map<String, dynamic> json) => IntraDayConfig(
        workWindows: (json['workWindows'] as List)
            .map((w) => TimeWindow.fromJson(w as Map<String, dynamic>))
            .toList(),
        hasLunchGap: json['hasLunchGap'] as bool? ?? true,
        lateNightProbability: (json['lateNightProbability'] as num?)?.toDouble() ?? 0.03,
      );
}

// ============================================================================
// BEHAVIOR CONFIG
// ============================================================================

class BehaviorConfig {
  final DateRange dateRange;
  final double averageIntensity; // Mean commits per day
  final Map<int, double> weekdayWeights; // 1=Mon..7=Sun, default 1.0
  final List<double> monthlyTrend; // 12 values, multipliers per month
  final double trendSlope; // Gradual increase over time (0.0 = flat, 0.1 = 10% increase)
  final SamplingMode samplingMode;
  final int minPerDay;
  final int maxPerDay;
  final int jitter; // +/- random adjustment
  final List<DateTime> holidays; // Days with near-zero commits
  final HolidayRegion holidayRegion;
  final IntraDayConfig intraDayConfig;

  const BehaviorConfig({
    required this.dateRange,
    required this.averageIntensity,
    required this.weekdayWeights,
    required this.monthlyTrend,
    this.trendSlope = 0.05,
    required this.samplingMode,
    required this.minPerDay,
    required this.maxPerDay,
    this.jitter = 1,
    required this.holidays,
    this.holidayRegion = HolidayRegion.vietnam,
    this.intraDayConfig = IntraDayConfig.defaultConfig,
  });

  BehaviorConfig copyWith({
    DateRange? dateRange,
    double? averageIntensity,
    Map<int, double>? weekdayWeights,
    List<double>? monthlyTrend,
    double? trendSlope,
    SamplingMode? samplingMode,
    int? minPerDay,
    int? maxPerDay,
    int? jitter,
    List<DateTime>? holidays,
    HolidayRegion? holidayRegion,
    IntraDayConfig? intraDayConfig,
  }) =>
      BehaviorConfig(
        dateRange: dateRange ?? this.dateRange,
        averageIntensity: averageIntensity ?? this.averageIntensity,
        weekdayWeights: weekdayWeights ?? this.weekdayWeights,
        monthlyTrend: monthlyTrend ?? this.monthlyTrend,
        trendSlope: trendSlope ?? this.trendSlope,
        samplingMode: samplingMode ?? this.samplingMode,
        minPerDay: minPerDay ?? this.minPerDay,
        maxPerDay: maxPerDay ?? this.maxPerDay,
        jitter: jitter ?? this.jitter,
        holidays: holidays ?? this.holidays,
        holidayRegion: holidayRegion ?? this.holidayRegion,
        intraDayConfig: intraDayConfig ?? this.intraDayConfig,
      );

  Map<String, dynamic> toJson() => {
        'dateRange': dateRange.toJson(),
        'averageIntensity': averageIntensity,
        'weekdayWeights': weekdayWeights.map((k, v) => MapEntry(k.toString(), v)),
        'monthlyTrend': monthlyTrend,
        'trendSlope': trendSlope,
        'samplingMode': samplingMode.name,
        'minPerDay': minPerDay,
        'maxPerDay': maxPerDay,
        'jitter': jitter,
        'holidays': holidays.map((d) => d.toIso8601String()).toList(),
        'holidayRegion': holidayRegion.name,
        'intraDayConfig': intraDayConfig.toJson(),
      };

  factory BehaviorConfig.fromJson(Map<String, dynamic> json) => BehaviorConfig(
        dateRange: DateRange.fromJson(json['dateRange'] as Map<String, dynamic>),
        averageIntensity: (json['averageIntensity'] as num).toDouble(),
        weekdayWeights: (json['weekdayWeights'] as Map<String, dynamic>)
            .map((k, v) => MapEntry(int.parse(k), (v as num).toDouble())),
        monthlyTrend:
            (json['monthlyTrend'] as List).map((e) => (e as num).toDouble()).toList(),
        trendSlope: (json['trendSlope'] as num?)?.toDouble() ?? 0.05,
        samplingMode: SamplingMode.values.byName(json['samplingMode'] as String),
        minPerDay: json['minPerDay'] as int,
        maxPerDay: json['maxPerDay'] as int,
        jitter: json['jitter'] as int? ?? 1,
        holidays: (json['holidays'] as List).map((e) => DateTime.parse(e as String)).toList(),
        holidayRegion: HolidayRegion.values.byName(json['holidayRegion'] as String? ?? 'vietnam'),
        intraDayConfig: json['intraDayConfig'] != null
            ? IntraDayConfig.fromJson(json['intraDayConfig'] as Map<String, dynamic>)
            : IntraDayConfig.defaultConfig,
      );

  static BehaviorConfig defaultConfig(DateRange range) => BehaviorConfig(
        dateRange: range,
        averageIntensity: 3.0,
        weekdayWeights: {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 0.9, 6: 0.3, 7: 0.2},
        monthlyTrend: List.filled(12, 1.0),
        samplingMode: SamplingMode.poisson,
        minPerDay: 0,
        maxPerDay: 12,
        holidays: [],
      );
}

// ============================================================================
// PLANNED COMMIT MODELS
// ============================================================================

class PlannedCommit {
  final DateTime timestamp;
  final String message;
  final String? filePath; // File to be created/modified

  const PlannedCommit({
    required this.timestamp,
    required this.message,
    this.filePath,
  });

  Map<String, dynamic> toJson() => {
        'timestamp': timestamp.toIso8601String(),
        'message': message,
        'filePath': filePath,
      };

  factory PlannedCommit.fromJson(Map<String, dynamic> json) => PlannedCommit(
        timestamp: DateTime.parse(json['timestamp'] as String),
        message: json['message'] as String,
        filePath: json['filePath'] as String?,
      );
}

class PlannedDay {
  final DateTime day;
  final List<PlannedCommit> commits;
  final bool isHoliday;
  final bool isWeekend;

  const PlannedDay({
    required this.day,
    required this.commits,
    this.isHoliday = false,
    this.isWeekend = false,
  });

  int get count => commits.length;

  Map<String, dynamic> toJson() => {
        'day': day.toIso8601String(),
        'commits': commits.map((c) => c.toJson()).toList(),
        'isHoliday': isHoliday,
        'isWeekend': isWeekend,
      };

  factory PlannedDay.fromJson(Map<String, dynamic> json) => PlannedDay(
        day: DateTime.parse(json['day'] as String),
        commits:
            (json['commits'] as List).map((c) => PlannedCommit.fromJson(c as Map<String, dynamic>)).toList(),
        isHoliday: json['isHoliday'] as bool? ?? false,
        isWeekend: json['isWeekend'] as bool? ?? false,
      );
}

// ============================================================================
// PLAN SUMMARY
// ============================================================================

class PlanSummary {
  final List<PlannedDay> days;
  final BehaviorConfig config;

  const PlanSummary({required this.days, required this.config});

  int get totalCommits => days.map((d) => d.count).sum;
  int get totalDays => days.length;
  int get activeDays => days.where((d) => d.count > 0).length;

  double get weekendRatio {
    final weekendCommits = days.where((d) => d.isWeekend).map((d) => d.count).sum;
    return totalCommits > 0 ? weekendCommits / totalCommits : 0;
  }

  double get averagePerDay => totalDays > 0 ? totalCommits / totalDays : 0;

  int get minPerDay => days.map((d) => d.count).minOrNull ?? 0;
  int get maxPerDay => days.map((d) => d.count).maxOrNull ?? 0;

  double get variance {
    if (days.isEmpty) return 0;
    final mean = averagePerDay;
    final squaredDiffs = days.map((d) => (d.count - mean) * (d.count - mean));
    return squaredDiffs.average;
  }

  List<PlannedCommit> get allCommits =>
      days.expand((d) => d.commits).toList()..sort((a, b) => a.timestamp.compareTo(b.timestamp));

  Map<String, dynamic> toJson() => {
        'days': days.map((d) => d.toJson()).toList(),
        'config': config.toJson(),
      };

  factory PlanSummary.fromJson(Map<String, dynamic> json) => PlanSummary(
        days:
            (json['days'] as List).map((d) => PlannedDay.fromJson(d as Map<String, dynamic>)).toList(),
        config: BehaviorConfig.fromJson(json['config'] as Map<String, dynamic>),
      );

  static PlanSummary get empty => PlanSummary(
        days: const [],
        config: BehaviorConfig(
          dateRange: DateRange(DateTime(2024), DateTime(2024)),
          averageIntensity: 0,
          weekdayWeights: const {},
          monthlyTrend: const [],
          samplingMode: SamplingMode.poisson,
          minPerDay: 0,
          maxPerDay: 0,
          holidays: const [],
        ),
      );
}

// ============================================================================
// RUN SNAPSHOT (for undo)
// ============================================================================

class RunSnapshot {
  final String id;
  final DateTime createdAt;
  final String headCommit; // SHA before run
  final String branch;
  final List<String> filesCreated;
  final int totalCommits;
  final bool pushed;
  final RunStatus status;
  final String repoPath;
  final PlanSummary plan;

  const RunSnapshot({
    required this.id,
    required this.createdAt,
    required this.headCommit,
    required this.branch,
    required this.filesCreated,
    required this.totalCommits,
    required this.pushed,
    required this.status,
    required this.repoPath,
    required this.plan,
  });

  RunSnapshot copyWith({
    String? id,
    DateTime? createdAt,
    String? headCommit,
    String? branch,
    List<String>? filesCreated,
    int? totalCommits,
    bool? pushed,
    RunStatus? status,
    String? repoPath,
    PlanSummary? plan,
  }) =>
      RunSnapshot(
        id: id ?? this.id,
        createdAt: createdAt ?? this.createdAt,
        headCommit: headCommit ?? this.headCommit,
        branch: branch ?? this.branch,
        filesCreated: filesCreated ?? this.filesCreated,
        totalCommits: totalCommits ?? this.totalCommits,
        pushed: pushed ?? this.pushed,
        status: status ?? this.status,
        repoPath: repoPath ?? this.repoPath,
        plan: plan ?? this.plan,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'createdAt': createdAt.toIso8601String(),
        'headCommit': headCommit,
        'branch': branch,
        'filesCreated': filesCreated,
        'totalCommits': totalCommits,
        'pushed': pushed,
        'status': status.name,
        'repoPath': repoPath,
        'plan': plan.toJson(),
      };

  factory RunSnapshot.fromJson(Map<String, dynamic> json) => RunSnapshot(
        id: json['id'] as String,
        createdAt: DateTime.parse(json['createdAt'] as String),
        headCommit: json['headCommit'] as String,
        branch: json['branch'] as String,
        filesCreated: (json['filesCreated'] as List).cast<String>(),
        totalCommits: json['totalCommits'] as int,
        pushed: json['pushed'] as bool,
        status: RunStatus.values.byName(json['status'] as String),
        repoPath: json['repoPath'] as String,
        plan: PlanSummary.fromJson(json['plan'] as Map<String, dynamic>),
      );
}

// ============================================================================
// GITHUB CONTRIBUTION DATA (for profile import)
// ============================================================================

class ContributionDay {
  final DateTime date;
  final int count;

  const ContributionDay({required this.date, required this.count});

  Map<String, dynamic> toJson() => {
        'date': date.toIso8601String(),
        'count': count,
      };

  factory ContributionDay.fromJson(Map<String, dynamic> json) => ContributionDay(
        date: DateTime.parse(json['date'] as String),
        count: json['count'] as int,
      );
}

class ContributionProfile {
  final String username;
  final List<ContributionDay> contributions;
  final DateTime fetchedAt;

  const ContributionProfile({
    required this.username,
    required this.contributions,
    required this.fetchedAt,
  });

  /// Calculate average intensity from profile
  double get averageIntensity {
    if (contributions.isEmpty) return 3.0;
    return contributions.map((c) => c.count).average;
  }

  /// Calculate weekday weights from profile
  Map<int, double> get weekdayWeights {
    final dayTotals = <int, List<int>>{};
    for (final c in contributions) {
      final weekday = c.date.weekday;
      dayTotals.putIfAbsent(weekday, () => []).add(c.count);
    }
    final avgByDay = dayTotals.map((k, v) => MapEntry(k, v.average));
    final maxAvg = avgByDay.values.maxOrNull ?? 1.0;
    return avgByDay.map((k, v) => MapEntry(k, maxAvg > 0 ? v / maxAvg : 1.0));
  }

  Map<String, dynamic> toJson() => {
        'username': username,
        'contributions': contributions.map((c) => c.toJson()).toList(),
        'fetchedAt': fetchedAt.toIso8601String(),
      };

  factory ContributionProfile.fromJson(Map<String, dynamic> json) => ContributionProfile(
        username: json['username'] as String,
        contributions: (json['contributions'] as List)
            .map((c) => ContributionDay.fromJson(c as Map<String, dynamic>))
            .toList(),
        fetchedAt: DateTime.parse(json['fetchedAt'] as String),
      );
}

// ============================================================================
// APP STATE
// ============================================================================

enum AppStep { repoPicker, identity, behaviorConfig, preview, run, history }

class AppState {
  final AppStep currentStep;
  final RepoConfig repoConfig;
  final IdentityConfig identityConfig;
  final BehaviorConfig? behaviorConfig;
  final PlanSummary? planSummary;
  final List<RunSnapshot> runHistory;
  final bool isRunning;
  final String? errorMessage;
  final ContributionProfile? contributionProfile;

  const AppState({
    this.currentStep = AppStep.repoPicker,
    this.repoConfig = RepoConfig.empty,
    this.identityConfig = IdentityConfig.empty,
    this.behaviorConfig,
    this.planSummary,
    this.runHistory = const [],
    this.isRunning = false,
    this.errorMessage,
    this.contributionProfile,
  });

  AppState copyWith({
    AppStep? currentStep,
    RepoConfig? repoConfig,
    IdentityConfig? identityConfig,
    BehaviorConfig? behaviorConfig,
    PlanSummary? planSummary,
    List<RunSnapshot>? runHistory,
    bool? isRunning,
    String? errorMessage,
    ContributionProfile? contributionProfile,
  }) =>
      AppState(
        currentStep: currentStep ?? this.currentStep,
        repoConfig: repoConfig ?? this.repoConfig,
        identityConfig: identityConfig ?? this.identityConfig,
        behaviorConfig: behaviorConfig ?? this.behaviorConfig,
        planSummary: planSummary ?? this.planSummary,
        runHistory: runHistory ?? this.runHistory,
        isRunning: isRunning ?? this.isRunning,
        errorMessage: errorMessage,
        contributionProfile: contributionProfile ?? this.contributionProfile,
      );
}
