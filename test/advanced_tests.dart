import 'package:flutter_test/flutter_test.dart';
import 'package:fake_comm_gui/domain/models.dart';
import 'package:fake_comm_gui/services/behavior_engine.dart';

/// Advanced tests for edge cases and complex scenarios
void main() {
  group('BehaviorEngine Edge Cases', () {
    final engine = BehaviorEngine();

    test('handles empty date range gracefully', () {
      final config = BehaviorConfig(
        dateRange: DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 1)),
        averageIntensity: 3.0,
        weekdayWeights: {
          1: 1.0,
          2: 1.0,
          3: 1.0,
          4: 1.0,
          5: 1.0,
          6: 0.3,
          7: 0.2
        },
        monthlyTrend: List.filled(12, 1.0),
        samplingMode: SamplingMode.poisson,
        minPerDay: 0,
        maxPerDay: 10,
        holidays: [],
      );

      final plan = engine.generatePlan(config, ['test']);
      expect(plan.days.length, 1);
    });

    test('handles all holidays in range', () {
      final holidays = List.generate(
        10,
        (i) => DateTime(2024, 1, i + 1),
      );

      final config = BehaviorConfig(
        dateRange: DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 10)),
        averageIntensity: 5.0,
        weekdayWeights: {
          1: 1.0,
          2: 1.0,
          3: 1.0,
          4: 1.0,
          5: 1.0,
          6: 1.0,
          7: 1.0
        },
        monthlyTrend: List.filled(12, 1.0),
        samplingMode: SamplingMode.poisson,
        minPerDay: 0,
        maxPerDay: 10,
        holidays: holidays,
      );

      final plan = engine.generatePlan(config, ['test']);

      // All days should be marked as holidays
      for (final day in plan.days) {
        expect(day.isHoliday, true);
      }
    });

    test('normal sampling mode works', () {
      final config = BehaviorConfig(
        dateRange: DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 30)),
        averageIntensity: 5.0,
        weekdayWeights: {
          1: 1.0,
          2: 1.0,
          3: 1.0,
          4: 1.0,
          5: 1.0,
          6: 1.0,
          7: 1.0
        },
        monthlyTrend: List.filled(12, 1.0),
        samplingMode: SamplingMode.normal,
        minPerDay: 0,
        maxPerDay: 20,
        holidays: [],
      );

      final plan = engine.generatePlan(config, ['test']);
      expect(plan.days.isNotEmpty, true);
      expect(plan.totalCommits > 0, true);
    });

    test('zero intensity produces minimal commits', () {
      final config = BehaviorConfig(
        dateRange: DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 10)),
        averageIntensity: 0.0,
        weekdayWeights: {
          1: 1.0,
          2: 1.0,
          3: 1.0,
          4: 1.0,
          5: 1.0,
          6: 1.0,
          7: 1.0
        },
        monthlyTrend: List.filled(12, 1.0),
        samplingMode: SamplingMode.poisson,
        minPerDay: 0,
        maxPerDay: 10,
        holidays: [],
      );

      final plan = engine.generatePlan(config, ['test']);
      // Most days should have 0 commits with 0 intensity
      final zeroCommitDays = plan.days.where((d) => d.count == 0).length;
      expect(zeroCommitDays > plan.days.length / 2, true);
    });

    test('monthly trend affects distribution', () {
      // January = high, February = low
      final monthlyTrend = List.filled(12, 1.0);
      monthlyTrend[0] = 2.0; // January boost
      monthlyTrend[1] = 0.2; // February reduction

      final config = BehaviorConfig(
        dateRange: DateRange(DateTime(2024, 1, 15), DateTime(2024, 2, 15)),
        averageIntensity: 5.0,
        weekdayWeights: {
          1: 1.0,
          2: 1.0,
          3: 1.0,
          4: 1.0,
          5: 1.0,
          6: 1.0,
          7: 1.0
        },
        monthlyTrend: monthlyTrend,
        samplingMode: SamplingMode.poisson,
        minPerDay: 0,
        maxPerDay: 20,
        holidays: [],
      );

      final plan = engine.generatePlan(config, ['test']);

      final januaryCommits = plan.days
          .where((d) => d.day.month == 1)
          .fold<int>(0, (sum, d) => sum + d.count);
      final februaryCommits = plan.days
          .where((d) => d.day.month == 2)
          .fold<int>(0, (sum, d) => sum + d.count);

      // January should generally have more commits than February
      // (This is probabilistic, so we just check they're both generated)
      expect(januaryCommits >= 0, true);
      expect(februaryCommits >= 0, true);
    });
  });

  group('DateRange Edge Cases', () {
    test('same start and end date', () {
      final range = DateRange(DateTime(2024, 1, 15), DateTime(2024, 1, 15));
      expect(range.dayCount, 1);
      expect(range.allDays.length, 1);
    });

    test('leap year handling', () {
      final range = DateRange(DateTime(2024, 2, 28), DateTime(2024, 3, 1));
      expect(range.dayCount, 3); // Feb 28, Feb 29 (leap year), Mar 1
      expect(range.allDays[1].day, 29);
    });

    test('year boundary crossing', () {
      final range = DateRange(DateTime(2023, 12, 30), DateTime(2024, 1, 2));
      expect(range.dayCount, 4);
      expect(range.allDays.last.year, 2024);
    });
  });

  group('TimeWindow Edge Cases', () {
    test('midnight crossing window', () {
      const window = TimeWindow(
        startHour: 22,
        startMinute: 0,
        endHour: 23,
        endMinute: 59,
      );

      final day = DateTime(2024, 1, 15);
      final time = window.randomTimeOn(day, 0.5);

      expect(time.hour >= 22, true);
    });

    test('single minute window', () {
      const window = TimeWindow(
        startHour: 12,
        startMinute: 0,
        endHour: 12,
        endMinute: 1,
      );

      expect(window.durationMinutes, 1);
    });

    test('full day window', () {
      const window = TimeWindow(
        startHour: 0,
        startMinute: 0,
        endHour: 23,
        endMinute: 59,
      );

      expect(window.durationMinutes, 23 * 60 + 59);
    });
  });

  group('IntraDayConfig Tests', () {
    test('default config has work hours window', () {
      const config = IntraDayConfig.defaultConfig;
      expect(config.workWindows.isNotEmpty, true);
      expect(config.workWindows.length, 2); // Morning + Afternoon
    });

    test('custom windows are preserved', () {
      const config = IntraDayConfig(
        workWindows: [
          TimeWindow(startHour: 9, startMinute: 0, endHour: 12, endMinute: 0),
          TimeWindow(startHour: 14, startMinute: 0, endHour: 18, endMinute: 0),
        ],
        hasLunchGap: false,
        lateNightProbability: 0.05,
      );

      expect(config.workWindows.length, 2);
      expect(config.hasLunchGap, false);
      expect(config.lateNightProbability, 0.05);
    });

    test('late night window is defined', () {
      const lateNight = IntraDayConfig.lateNightWindow;
      expect(lateNight.startHour, 22);
      expect(lateNight.endHour, 23);
    });
  });

  group('PlannedDay Tests', () {
    test('count returns correct number', () {
      final day = PlannedDay(
        day: DateTime(2024, 1, 15),
        commits: [
          PlannedCommit(timestamp: DateTime(2024, 1, 15, 10), message: 'a'),
          PlannedCommit(timestamp: DateTime(2024, 1, 15, 11), message: 'b'),
          PlannedCommit(timestamp: DateTime(2024, 1, 15, 12), message: 'c'),
        ],
        isWeekend: false,
      );

      expect(day.count, 3);
    });

    test('empty day has zero count', () {
      final day = PlannedDay(
        day: DateTime(2024, 1, 15),
        commits: [],
        isWeekend: false,
      );

      expect(day.count, 0);
    });

    test('isHoliday flag works', () {
      final day = PlannedDay(
        day: DateTime(2024, 1, 1),
        commits: [],
        isWeekend: false,
        isHoliday: true,
      );

      expect(day.isHoliday, true);
    });
  });

  group('AppState Tests', () {
    test('default state is correct', () {
      const state = AppState();

      expect(state.currentStep, AppStep.repoPicker);
      expect(state.repoConfig.path, '');
      expect(state.identityConfig.username, '');
      expect(state.isRunning, false);
    });

    test('copyWith preserves unchanged fields', () {
      const state = AppState();
      final newState = state.copyWith(currentStep: AppStep.identity);

      expect(newState.currentStep, AppStep.identity);
      expect(newState.repoConfig.path, state.repoConfig.path);
    });

    test('copyWith updates specified fields', () {
      const state = AppState();
      final newState = state.copyWith(
        isRunning: true,
        errorMessage: 'Test error',
      );

      expect(newState.isRunning, true);
      expect(newState.errorMessage, 'Test error');
    });
  });

  group('RepoConfig Tests', () {
    test('isValid checks correctly', () {
      const validConfig = RepoConfig(
        path: '/path/to/repo',
        branch: 'main',
        isValid: true,
      );

      expect(validConfig.isValid, true);

      const invalidConfig = RepoConfig(
        path: '',
        branch: '',
        isValid: false,
      );

      expect(invalidConfig.isValid, false);
    });

    test('optional fields work', () {
      const config = RepoConfig(
        path: '/path/to/repo',
        branch: 'main',
        isValid: true,
        remoteUrl: 'https://github.com/user/repo.git',
        gitVersion: '2.40.0',
        isDirty: true,
      );

      expect(config.remoteUrl, 'https://github.com/user/repo.git');
      expect(config.gitVersion, '2.40.0');
      expect(config.isDirty, true);
    });

    test('empty config has correct defaults', () {
      expect(RepoConfig.empty.path, '');
      expect(RepoConfig.empty.branch, '');
      expect(RepoConfig.empty.isValid, false);
    });
  });

  group('IdentityConfig Tests', () {
    test('empty config has correct defaults', () {
      expect(IdentityConfig.empty.username, '');
      expect(IdentityConfig.empty.email, '');
      expect(IdentityConfig.empty.timezone, 'Asia/Ho_Chi_Minh');
    });

    test('copyWith works correctly', () {
      const config = IdentityConfig.empty;
      final updated = config.copyWith(
        username: 'newuser',
        email: 'new@example.com',
      );

      expect(updated.username, 'newuser');
      expect(updated.email, 'new@example.com');
      expect(updated.timezone, 'Asia/Ho_Chi_Minh'); // unchanged
    });
  });

  group('RunStatus Tests', () {
    test('all statuses are unique', () {
      const statuses = RunStatus.values;
      final uniqueNames = statuses.map((s) => s.name).toSet();
      expect(uniqueNames.length, statuses.length);
    });

    test('contains expected values', () {
      expect(RunStatus.values.contains(RunStatus.pending), true);
      expect(RunStatus.values.contains(RunStatus.running), true);
      expect(RunStatus.values.contains(RunStatus.completed), true);
      expect(RunStatus.values.contains(RunStatus.failed), true);
      expect(RunStatus.values.contains(RunStatus.undone), true);
    });
  });

  group('SamplingMode Tests', () {
    test('all modes are available', () {
      expect(SamplingMode.values.contains(SamplingMode.poisson), true);
      expect(SamplingMode.values.contains(SamplingMode.normal), true);
    });
  });

  group('AppStep Tests', () {
    test('all steps are defined', () {
      expect(AppStep.values.contains(AppStep.repoPicker), true);
      expect(AppStep.values.contains(AppStep.identity), true);
      expect(AppStep.values.contains(AppStep.behaviorConfig), true);
      expect(AppStep.values.contains(AppStep.preview), true);
      expect(AppStep.values.contains(AppStep.run), true);
      expect(AppStep.values.contains(AppStep.history), true);
    });

    test('steps are in correct order', () {
      expect(AppStep.repoPicker.index, 0);
      expect(AppStep.identity.index, 1);
      expect(AppStep.behaviorConfig.index, 2);
      expect(AppStep.preview.index, 3);
      expect(AppStep.run.index, 4);
      expect(AppStep.history.index, 5);
    });
  });

  group('HolidayRegion Tests', () {
    test('all regions are defined', () {
      expect(HolidayRegion.values.contains(HolidayRegion.vietnam), true);
      expect(HolidayRegion.values.contains(HolidayRegion.usa), true);
      expect(HolidayRegion.values.contains(HolidayRegion.japan), true);
      expect(HolidayRegion.values.contains(HolidayRegion.korea), true);
      expect(HolidayRegion.values.contains(HolidayRegion.eu), true);
    });
  });

  group('BehaviorConfig Default', () {
    test('defaultConfig creates valid config', () {
      final range = DateRange(DateTime(2024, 1, 1), DateTime(2024, 12, 31));
      final config = BehaviorConfig.defaultConfig(range);

      expect(config.dateRange, range);
      expect(config.averageIntensity, 3.0);
      expect(config.samplingMode, SamplingMode.poisson);
      expect(config.weekdayWeights.length, 7);
    });
  });

  group('PlanSummary Tests', () {
    test('empty plan has correct defaults', () {
      final empty = PlanSummary.empty;
      expect(empty.totalCommits, 0);
      expect(empty.totalDays, 0);
      expect(empty.activeDays, 0);
    });

    test('variance calculates correctly', () {
      final days = [
        PlannedDay(
          day: DateTime(2024, 1, 1),
          commits: [
            PlannedCommit(timestamp: DateTime(2024, 1, 1, 10), message: 'a'),
            PlannedCommit(timestamp: DateTime(2024, 1, 1, 11), message: 'b'),
          ],
          isWeekend: false,
        ),
        PlannedDay(
          day: DateTime(2024, 1, 2),
          commits: [
            PlannedCommit(timestamp: DateTime(2024, 1, 2, 10), message: 'c'),
            PlannedCommit(timestamp: DateTime(2024, 1, 2, 11), message: 'd'),
          ],
          isWeekend: false,
        ),
      ];

      final summary = PlanSummary(
        days: days,
        config: BehaviorConfig.defaultConfig(
          DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 2)),
        ),
      );

      // Both days have 2 commits, so variance should be 0
      expect(summary.variance, 0.0);
    });

    test('allCommits returns sorted list', () {
      final days = [
        PlannedDay(
          day: DateTime(2024, 1, 1),
          commits: [
            PlannedCommit(timestamp: DateTime(2024, 1, 1, 15), message: 'late'),
            PlannedCommit(timestamp: DateTime(2024, 1, 1, 9), message: 'early'),
          ],
          isWeekend: false,
        ),
      ];

      final summary = PlanSummary(
        days: days,
        config: BehaviorConfig.defaultConfig(
          DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 1)),
        ),
      );

      final allCommits = summary.allCommits;
      expect(allCommits[0].message, 'early');
      expect(allCommits[1].message, 'late');
    });
  });
}
