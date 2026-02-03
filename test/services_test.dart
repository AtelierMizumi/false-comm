import 'package:flutter_test/flutter_test.dart';
import 'package:fake_comm_gui/domain/models.dart';
import 'package:fake_comm_gui/services/behavior_engine.dart';
import 'package:fake_comm_gui/services/holiday_service.dart';
import 'package:fake_comm_gui/services/content_generator.dart';

void main() {
  group('DateRange Tests', () {
    test('dayCount calculates correctly', () {
      final range = DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 10));
      expect(range.dayCount, 10);
    });

    test('allDays returns correct list', () {
      final range = DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 3));
      final days = range.allDays;
      expect(days.length, 3);
      expect(days[0], DateTime(2024, 1, 1));
      expect(days[1], DateTime(2024, 1, 2));
      expect(days[2], DateTime(2024, 1, 3));
    });

    test('contains works correctly', () {
      final range = DateRange(DateTime(2024, 1, 5), DateTime(2024, 1, 10));
      expect(range.contains(DateTime(2024, 1, 7)), true);
      expect(range.contains(DateTime(2024, 1, 1)), false);
      expect(range.contains(DateTime(2024, 1, 15)), false);
    });
  });

  group('HolidayService Tests', () {
    const holidayService = HolidayService();

    test('Vietnam holidays include Tet', () {
      final range = DateRange(DateTime(2024, 1, 1), DateTime(2024, 12, 31));
      final holidays = holidayService.getHolidays(HolidayRegion.vietnam, range);

      expect(holidays.isNotEmpty, true);
      // Should include New Year
      expect(holidays.any((h) => h.month == 1 && h.day == 1), true);
      // Should include Reunification Day (April 30)
      expect(holidays.any((h) => h.month == 4 && h.day == 30), true);
      // Should include National Day (September 2)
      expect(holidays.any((h) => h.month == 9 && h.day == 2), true);
    });

    test('USA holidays include July 4th', () {
      final range = DateRange(DateTime(2024, 1, 1), DateTime(2024, 12, 31));
      final holidays = holidayService.getHolidays(HolidayRegion.usa, range);

      expect(holidays.any((h) => h.month == 7 && h.day == 4), true);
      expect(holidays.any((h) => h.month == 12 && h.day == 25), true);
    });

    test('Japan holidays include New Year period', () {
      final range = DateRange(DateTime(2024, 1, 1), DateTime(2024, 12, 31));
      final holidays = holidayService.getHolidays(HolidayRegion.japan, range);

      expect(holidays.any((h) => h.month == 1 && h.day == 1), true);
      expect(holidays.any((h) => h.month == 1 && h.day == 2), true);
      expect(holidays.any((h) => h.month == 1 && h.day == 3), true);
    });

    test('isHoliday returns correct result', () {
      expect(
        holidayService.isHoliday(DateTime(2024, 1, 1), HolidayRegion.vietnam),
        true,
      );
      expect(
        holidayService.isHoliday(DateTime(2024, 3, 15), HolidayRegion.vietnam),
        false,
      );
    });

    test('region names are correct', () {
      expect(holidayService.getRegionName(HolidayRegion.vietnam), 'Vietnam');
      expect(holidayService.getRegionName(HolidayRegion.usa), 'United States');
      expect(holidayService.getRegionName(HolidayRegion.japan), 'Japan');
    });
  });

  group('BehaviorEngine Tests', () {
    final engine = BehaviorEngine();

    test('generates plan with correct number of days', () {
      final config = BehaviorConfig(
        dateRange: DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 10)),
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

      final messages = ['chore: update notes', 'docs: add findings'];
      final plan = engine.generatePlan(config, messages);

      expect(plan.days.length, 10);
      expect(plan.totalDays, 10);
    });

    test('holidays have near-zero commits', () {
      final holiday = DateTime(2024, 1, 5);
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
        maxPerDay: 20,
        holidays: [holiday],
      );

      final messages = ['chore: update'];
      final plan = engine.generatePlan(config, messages);

      // Find the holiday day
      final holidayPlan = plan.days.firstWhere(
        (d) =>
            d.day.year == holiday.year &&
            d.day.month == holiday.month &&
            d.day.day == holiday.day,
      );

      expect(holidayPlan.isHoliday, true);
      expect(holidayPlan.count <= 1, true); // 0 or 1 commits on holiday
    });

    test('weekends are correctly marked', () {
      // Jan 6, 2024 is a Saturday
      // Jan 7, 2024 is a Sunday
      final config = BehaviorConfig(
        dateRange: DateRange(DateTime(2024, 1, 6), DateTime(2024, 1, 7)),
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

      expect(plan.days[0].isWeekend, true); // Saturday
      expect(plan.days[1].isWeekend, true); // Sunday
    });

    test('respects min/max caps', () {
      final config = BehaviorConfig(
        dateRange: DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 30)),
        averageIntensity: 10.0, // High intensity
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
        minPerDay: 2,
        maxPerDay: 8,
        holidays: [],
      );

      final plan = engine.generatePlan(config, ['test']);

      for (final day in plan.days) {
        expect(day.count >= 2, true, reason: 'Count should be >= min (2)');
        expect(day.count <= 8, true, reason: 'Count should be <= max (8)');
      }
    });

    test('blendWithProfile adjusts intensity', () {
      final config = BehaviorConfig(
        dateRange: DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 10)),
        averageIntensity: 2.0,
        weekdayWeights: {
          1: 1.0,
          2: 1.0,
          3: 1.0,
          4: 1.0,
          5: 1.0,
          6: 0.5,
          7: 0.5
        },
        monthlyTrend: List.filled(12, 1.0),
        samplingMode: SamplingMode.poisson,
        minPerDay: 0,
        maxPerDay: 10,
        holidays: [],
      );

      final profile = ContributionProfile(
        username: 'testuser',
        contributions: [
          ContributionDay(date: DateTime(2024, 1, 1), count: 6), // Monday
          ContributionDay(date: DateTime(2024, 1, 2), count: 6), // Tuesday
          ContributionDay(date: DateTime(2024, 1, 6), count: 2), // Saturday
          ContributionDay(date: DateTime(2024, 1, 7), count: 1), // Sunday
        ],
        fetchedAt: DateTime.now(),
      );

      final blended =
          engine.blendWithProfile(config, profile, profileWeight: 0.5);

      // Blended intensity should be between config (2.0) and profile average
      expect(blended.averageIntensity > 2.0, true);
    });
  });

  group('ContentGeneratorService Tests', () {
    test('has default commit messages', () {
      final generator = ContentGeneratorService();
      expect(generator.commitMessages.isNotEmpty, true);
      expect(generator.commitMessages.length, 20);
    });

    test('getRandomMessage returns valid message', () {
      final generator = ContentGeneratorService();
      final message = generator.getRandomMessage();
      expect(message.isNotEmpty, true);
      expect(generator.commitMessages.contains(message), true);
    });

    test('supports custom messages', () {
      final customMessages = ['custom: message 1', 'custom: message 2'];
      final generator = ContentGeneratorService(customMessages: customMessages);
      expect(generator.commitMessages.length, 2);
      expect(generator.commitMessages, customMessages);
    });
  });

  group('TimeWindow Tests', () {
    test('durationMinutes calculates correctly', () {
      const window = TimeWindow(
        startHour: 9,
        startMinute: 30,
        endHour: 12,
        endMinute: 0,
      );
      expect(window.durationMinutes, 150); // 2.5 hours
    });

    test('toString formats correctly', () {
      const window = TimeWindow(
        startHour: 9,
        startMinute: 30,
        endHour: 18,
        endMinute: 30,
      );
      expect(window.toString(), '09:30-18:30');
    });

    test('randomTimeOn generates valid time', () {
      const window = TimeWindow(
        startHour: 10,
        startMinute: 0,
        endHour: 11,
        endMinute: 0,
      );
      final day = DateTime(2024, 1, 15);
      final time = window.randomTimeOn(day, 0.5);

      expect(time.year, 2024);
      expect(time.month, 1);
      expect(time.day, 15);
      expect(time.hour >= 10 && time.hour <= 11, true);
    });
  });

  group('PlanSummary Tests', () {
    test('statistics calculate correctly', () {
      final days = [
        PlannedDay(
          day: DateTime(2024, 1, 1),
          commits: [
            PlannedCommit(timestamp: DateTime(2024, 1, 1, 10), message: 'test'),
            PlannedCommit(timestamp: DateTime(2024, 1, 1, 11), message: 'test'),
          ],
          isWeekend: false,
        ),
        PlannedDay(
          day: DateTime(2024, 1, 2),
          commits: [
            PlannedCommit(timestamp: DateTime(2024, 1, 2, 10), message: 'test'),
          ],
          isWeekend: false,
        ),
        PlannedDay(
          day: DateTime(2024, 1, 6), // Saturday
          commits: [
            PlannedCommit(timestamp: DateTime(2024, 1, 6, 10), message: 'test'),
          ],
          isWeekend: true,
        ),
      ];

      final config = BehaviorConfig(
        dateRange: DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 6)),
        averageIntensity: 2.0,
        weekdayWeights: {},
        monthlyTrend: [],
        samplingMode: SamplingMode.poisson,
        minPerDay: 0,
        maxPerDay: 10,
        holidays: [],
      );

      final summary = PlanSummary(days: days, config: config);

      expect(summary.totalCommits, 4);
      expect(summary.totalDays, 3);
      expect(summary.activeDays, 3);
      expect(summary.minPerDay, 1);
      expect(summary.maxPerDay, 2);
      expect(summary.weekendRatio, 0.25); // 1 out of 4 commits on weekend
    });
  });

  group('Model Serialization Tests', () {
    test('IdentityConfig toJson and fromJson', () {
      const config = IdentityConfig(
        username: 'testuser',
        email: 'test@example.com',
        timezone: 'Asia/Ho_Chi_Minh',
      );

      final json = config.toJson();
      final restored = IdentityConfig.fromJson(json);

      expect(restored.username, config.username);
      expect(restored.email, config.email);
      expect(restored.timezone, config.timezone);
    });

    test('DateRange toJson and fromJson', () {
      final range = DateRange(DateTime(2024, 1, 1), DateTime(2024, 12, 31));
      final json = range.toJson();
      final restored = DateRange.fromJson(json);

      expect(restored.start, range.start);
      expect(restored.end, range.end);
    });

    test('PlannedCommit toJson and fromJson', () {
      final commit = PlannedCommit(
        timestamp: DateTime(2024, 1, 15, 10, 30),
        message: 'chore: update notes',
        filePath: 'notes/2024-01-15.md',
      );

      final json = commit.toJson();
      final restored = PlannedCommit.fromJson(json);

      expect(restored.timestamp, commit.timestamp);
      expect(restored.message, commit.message);
      expect(restored.filePath, commit.filePath);
    });

    test('RunSnapshot toJson and fromJson', () {
      final snapshot = RunSnapshot(
        id: 'test-123',
        createdAt: DateTime(2024, 1, 15, 10, 30),
        headCommit: 'abc123def456',
        branch: 'main',
        filesCreated: ['notes/2024-01-15.md', 'progress.json'],
        totalCommits: 5,
        pushed: true,
        status: RunStatus.completed,
        repoPath: '/path/to/repo',
        plan: PlanSummary(
          days: [],
          config: BehaviorConfig(
            dateRange: DateRange(DateTime(2024, 1, 1), DateTime(2024, 1, 10)),
            averageIntensity: 3.0,
            weekdayWeights: {},
            monthlyTrend: [],
            samplingMode: SamplingMode.poisson,
            minPerDay: 0,
            maxPerDay: 10,
            holidays: [],
          ),
        ),
      );

      final json = snapshot.toJson();
      final restored = RunSnapshot.fromJson(json);

      expect(restored.id, snapshot.id);
      expect(restored.headCommit, snapshot.headCommit);
      expect(restored.branch, snapshot.branch);
      expect(restored.filesCreated, snapshot.filesCreated);
      expect(restored.totalCommits, snapshot.totalCommits);
      expect(restored.pushed, snapshot.pushed);
      expect(restored.status, snapshot.status);
    });
  });

  group('ContributionProfile Tests', () {
    test('averageIntensity calculates correctly', () {
      final profile = ContributionProfile(
        username: 'testuser',
        contributions: [
          ContributionDay(date: DateTime(2024, 1, 1), count: 4),
          ContributionDay(date: DateTime(2024, 1, 2), count: 6),
          ContributionDay(date: DateTime(2024, 1, 3), count: 2),
        ],
        fetchedAt: DateTime.now(),
      );

      expect(profile.averageIntensity, 4.0); // (4+6+2)/3 = 4
    });

    test('weekdayWeights calculates correctly', () {
      final profile = ContributionProfile(
        username: 'testuser',
        contributions: [
          // Monday (day 1)
          ContributionDay(date: DateTime(2024, 1, 1), count: 10),
          ContributionDay(date: DateTime(2024, 1, 8), count: 10),
          // Saturday (day 6)
          ContributionDay(date: DateTime(2024, 1, 6), count: 2),
          ContributionDay(date: DateTime(2024, 1, 13), count: 2),
        ],
        fetchedAt: DateTime.now(),
      );

      final weights = profile.weekdayWeights;

      // Monday should have weight 1.0 (highest)
      expect(weights[1], 1.0);
      // Saturday should have weight 0.2 (2/10)
      expect(weights[6], 0.2);
    });
  });
}
