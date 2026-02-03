import '../domain/models.dart';

/// Service providing preset holidays for multiple regions.
/// Includes Vietnam, USA, Japan, Korea, and EU common holidays.
class HolidayService {
  const HolidayService();

  /// Get all holidays for a region within a date range
  List<DateTime> getHolidays(HolidayRegion region, DateRange range) {
    final allHolidays = <DateTime>[];

    for (var year = range.start.year; year <= range.end.year; year++) {
      final yearHolidays = _getHolidaysForYear(region, year);
      allHolidays.addAll(yearHolidays.where((d) => range.contains(d)));
    }

    return allHolidays..sort();
  }

  /// Get holidays for a specific year and region
  List<DateTime> _getHolidaysForYear(HolidayRegion region, int year) {
    switch (region) {
      case HolidayRegion.vietnam:
        return _vietnamHolidays(year);
      case HolidayRegion.usa:
        return _usaHolidays(year);
      case HolidayRegion.japan:
        return _japanHolidays(year);
      case HolidayRegion.korea:
        return _koreaHolidays(year);
      case HolidayRegion.eu:
        return _euHolidays(year);
    }
  }

  /// Get display name for a region
  String getRegionName(HolidayRegion region) {
    switch (region) {
      case HolidayRegion.vietnam:
        return 'Vietnam';
      case HolidayRegion.usa:
        return 'United States';
      case HolidayRegion.japan:
        return 'Japan';
      case HolidayRegion.korea:
        return 'South Korea';
      case HolidayRegion.eu:
        return 'European Union';
    }
  }

  /// Vietnam public holidays
  List<DateTime> _vietnamHolidays(int year) {
    final holidays = <DateTime>[
      // New Year's Day
      DateTime(year, 1, 1),

      // Tet (Lunar New Year) - approximate, typically late Jan/early Feb
      // Using fixed approximation since exact dates vary
      ..._tetHolidays(year),

      // Hung Kings Commemoration Day (10th day of 3rd lunar month) ~April
      DateTime(year, 4, 18), // Approximate

      // Reunification Day
      DateTime(year, 4, 30),

      // International Workers' Day
      DateTime(year, 5, 1),

      // National Day
      DateTime(year, 9, 2),
      DateTime(year, 9, 3), // Additional day off
    ];

    return holidays;
  }

  /// Tet holidays (approximate - varies each year based on lunar calendar)
  List<DateTime> _tetHolidays(int year) {
    // Approximate Tet dates (actual dates depend on lunar calendar)
    // Typically 5-7 days off around late January/early February
    final tetApprox = _approximateTetDate(year);
    return [
      tetApprox.subtract(const Duration(days: 1)),
      tetApprox,
      tetApprox.add(const Duration(days: 1)),
      tetApprox.add(const Duration(days: 2)),
      tetApprox.add(const Duration(days: 3)),
      tetApprox.add(const Duration(days: 4)),
    ];
  }

  DateTime _approximateTetDate(int year) {
    // Rough approximation of Tet (Lunar New Year) dates
    // In reality, this varies between late January and mid-February
    final tetDates = {
      2023: DateTime(2023, 1, 22),
      2024: DateTime(2024, 2, 10),
      2025: DateTime(2025, 1, 29),
      2026: DateTime(2026, 2, 17),
      2027: DateTime(2027, 2, 6),
      2028: DateTime(2028, 1, 26),
      2029: DateTime(2029, 2, 13),
      2030: DateTime(2030, 2, 3),
    };
    return tetDates[year] ?? DateTime(year, 2, 1); // Default to Feb 1
  }

  /// USA Federal holidays
  List<DateTime> _usaHolidays(int year) {
    return [
      // New Year's Day
      DateTime(year, 1, 1),

      // Martin Luther King Jr. Day (3rd Monday of January)
      _nthWeekdayOfMonth(year, 1, DateTime.monday, 3),

      // Presidents' Day (3rd Monday of February)
      _nthWeekdayOfMonth(year, 2, DateTime.monday, 3),

      // Memorial Day (Last Monday of May)
      _lastWeekdayOfMonth(year, 5, DateTime.monday),

      // Independence Day
      DateTime(year, 7, 4),

      // Labor Day (1st Monday of September)
      _nthWeekdayOfMonth(year, 9, DateTime.monday, 1),

      // Columbus Day (2nd Monday of October)
      _nthWeekdayOfMonth(year, 10, DateTime.monday, 2),

      // Veterans Day
      DateTime(year, 11, 11),

      // Thanksgiving (4th Thursday of November)
      _nthWeekdayOfMonth(year, 11, DateTime.thursday, 4),

      // Christmas Day
      DateTime(year, 12, 25),
    ];
  }

  /// Japan public holidays
  List<DateTime> _japanHolidays(int year) {
    return [
      // New Year's Day
      DateTime(year, 1, 1),
      DateTime(year, 1, 2),
      DateTime(year, 1, 3),

      // Coming of Age Day (2nd Monday of January)
      _nthWeekdayOfMonth(year, 1, DateTime.monday, 2),

      // National Foundation Day
      DateTime(year, 2, 11),

      // Emperor's Birthday
      DateTime(year, 2, 23),

      // Vernal Equinox Day (~March 20-21)
      DateTime(year, 3, 20),

      // Showa Day
      DateTime(year, 4, 29),

      // Constitution Memorial Day
      DateTime(year, 5, 3),

      // Greenery Day
      DateTime(year, 5, 4),

      // Children's Day
      DateTime(year, 5, 5),

      // Marine Day (3rd Monday of July)
      _nthWeekdayOfMonth(year, 7, DateTime.monday, 3),

      // Mountain Day
      DateTime(year, 8, 11),

      // Respect for the Aged Day (3rd Monday of September)
      _nthWeekdayOfMonth(year, 9, DateTime.monday, 3),

      // Autumnal Equinox Day (~September 22-23)
      DateTime(year, 9, 23),

      // Sports Day (2nd Monday of October)
      _nthWeekdayOfMonth(year, 10, DateTime.monday, 2),

      // Culture Day
      DateTime(year, 11, 3),

      // Labor Thanksgiving Day
      DateTime(year, 11, 23),
    ];
  }

  /// South Korea public holidays
  List<DateTime> _koreaHolidays(int year) {
    final lunarNewYear = _approximateTetDate(year); // Same lunar calendar basis

    return [
      // New Year's Day
      DateTime(year, 1, 1),

      // Seollal (Lunar New Year) - 3 days
      lunarNewYear.subtract(const Duration(days: 1)),
      lunarNewYear,
      lunarNewYear.add(const Duration(days: 1)),

      // Independence Movement Day
      DateTime(year, 3, 1),

      // Children's Day
      DateTime(year, 5, 5),

      // Buddha's Birthday (varies, ~May)
      DateTime(year, 5, 15), // Approximate

      // Memorial Day
      DateTime(year, 6, 6),

      // Liberation Day
      DateTime(year, 8, 15),

      // Chuseok (Korean Thanksgiving) - 3 days, ~September
      DateTime(year, 9, 16), // Approximate
      DateTime(year, 9, 17),
      DateTime(year, 9, 18),

      // National Foundation Day
      DateTime(year, 10, 3),

      // Hangul Day
      DateTime(year, 10, 9),

      // Christmas Day
      DateTime(year, 12, 25),
    ];
  }

  /// EU common holidays (varies by country, using common ones)
  List<DateTime> _euHolidays(int year) {
    final easter = _calculateEaster(year);

    return [
      // New Year's Day
      DateTime(year, 1, 1),

      // Good Friday
      easter.subtract(const Duration(days: 2)),

      // Easter Monday
      easter.add(const Duration(days: 1)),

      // Labour Day
      DateTime(year, 5, 1),

      // Ascension Day (39 days after Easter)
      easter.add(const Duration(days: 39)),

      // Whit Monday (50 days after Easter)
      easter.add(const Duration(days: 50)),

      // Assumption of Mary
      DateTime(year, 8, 15),

      // All Saints' Day
      DateTime(year, 11, 1),

      // Christmas Day
      DateTime(year, 12, 25),

      // St. Stephen's Day / Boxing Day
      DateTime(year, 12, 26),
    ];
  }

  /// Calculate nth weekday of a month
  DateTime _nthWeekdayOfMonth(int year, int month, int weekday, int n) {
    var date = DateTime(year, month, 1);
    var count = 0;

    while (count < n) {
      if (date.weekday == weekday) {
        count++;
        if (count == n) return date;
      }
      date = date.add(const Duration(days: 1));
    }

    return date;
  }

  /// Calculate last weekday of a month
  DateTime _lastWeekdayOfMonth(int year, int month, int weekday) {
    var date = DateTime(year, month + 1, 0); // Last day of month

    while (date.weekday != weekday) {
      date = date.subtract(const Duration(days: 1));
    }

    return date;
  }

  /// Calculate Easter Sunday using the Anonymous Gregorian algorithm
  DateTime _calculateEaster(int year) {
    final a = year % 19;
    final b = year ~/ 100;
    final c = year % 100;
    final d = b ~/ 4;
    final e = b % 4;
    final f = (b + 8) ~/ 25;
    final g = (b - f + 1) ~/ 3;
    final h = (19 * a + b - d - g + 15) % 30;
    final i = c ~/ 4;
    final k = c % 4;
    final l = (32 + 2 * e + 2 * i - h - k) % 7;
    final m = (a + 11 * h + 22 * l) ~/ 451;
    final month = (h + l - 7 * m + 114) ~/ 31;
    final day = ((h + l - 7 * m + 114) % 31) + 1;

    return DateTime(year, month, day);
  }

  /// Check if a date is a holiday
  bool isHoliday(DateTime date, HolidayRegion region) {
    final year = date.year;
    final holidays = _getHolidaysForYear(region, year);
    return holidays.any((h) =>
        h.year == date.year && h.month == date.month && h.day == date.day);
  }

  /// Merge custom holidays with region presets
  List<DateTime> mergeHolidays(
    HolidayRegion region,
    DateRange range,
    List<DateTime> customHolidays,
  ) {
    final presets = getHolidays(region, range);
    final all = {...presets, ...customHolidays}.toList();
    all.sort();
    return all;
  }
}
