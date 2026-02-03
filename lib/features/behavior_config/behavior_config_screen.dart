import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../domain/models.dart';
import '../../providers/providers.dart';

class BehaviorConfigScreen extends ConsumerStatefulWidget {
  final VoidCallback onNext;
  final VoidCallback onBack;

  const BehaviorConfigScreen({
    super.key,
    required this.onNext,
    required this.onBack,
  });

  @override
  ConsumerState<BehaviorConfigScreen> createState() =>
      _BehaviorConfigScreenState();
}

class _BehaviorConfigScreenState extends ConsumerState<BehaviorConfigScreen> {
  DateTime _startDate = DateTime.now().subtract(const Duration(days: 90));
  DateTime _endDate = DateTime.now().subtract(const Duration(days: 1));
  double _avgIntensity = 3.0;
  SamplingMode _samplingMode = SamplingMode.poisson;
  HolidayRegion _holidayRegion = HolidayRegion.vietnam;
  int _minPerDay = 0;
  int _maxPerDay = 12;
  int _jitter = 1;
  double _trendSlope = 0.05;

  // Weekday weights (1=Mon..7=Sun)
  final Map<int, double> _weekdayWeights = {
    1: 1.0,
    2: 1.0,
    3: 1.0,
    4: 1.0,
    5: 0.9,
    6: 0.3,
    7: 0.2,
  };

  // Monthly trend multipliers
  final List<double> _monthlyTrend = List.filled(12, 1.0);

  @override
  void initState() {
    super.initState();
    // Load existing config if any
    final existingConfig = ref.read(behaviorConfigProvider);
    if (existingConfig != null) {
      _startDate = existingConfig.dateRange.start;
      _endDate = existingConfig.dateRange.end;
      _avgIntensity = existingConfig.averageIntensity;
      _samplingMode = existingConfig.samplingMode;
      _holidayRegion = existingConfig.holidayRegion;
      _minPerDay = existingConfig.minPerDay;
      _maxPerDay = existingConfig.maxPerDay;
      _jitter = existingConfig.jitter;
      _trendSlope = existingConfig.trendSlope;
      _weekdayWeights.addAll(existingConfig.weekdayWeights);
      for (var i = 0; i < 12 && i < existingConfig.monthlyTrend.length; i++) {
        _monthlyTrend[i] = existingConfig.monthlyTrend[i];
      }
    }
  }

  Future<void> _selectDateRange() async {
    final result = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
      initialDateRange: DateTimeRange(start: _startDate, end: _endDate),
    );

    if (result != null) {
      setState(() {
        _startDate = result.start;
        _endDate = result.end;
      });
    }
  }

  void _proceed() {
    final holidayService = ref.read(holidayServiceProvider);
    final dateRange = DateRange(_startDate, _endDate);
    final holidays = holidayService.getHolidays(_holidayRegion, dateRange);

    final config = BehaviorConfig(
      dateRange: dateRange,
      averageIntensity: _avgIntensity,
      weekdayWeights: Map.from(_weekdayWeights),
      monthlyTrend: List.from(_monthlyTrend),
      trendSlope: _trendSlope,
      samplingMode: _samplingMode,
      minPerDay: _minPerDay,
      maxPerDay: _maxPerDay,
      jitter: _jitter,
      holidays: holidays,
      holidayRegion: _holidayRegion,
    );

    ref.read(appStateProvider.notifier).setBehaviorConfig(config);

    // Generate preview
    final engine = ref.read(behaviorEngineProvider);
    final contentGen = ref.read(contentGeneratorProvider);
    final profile = ref.read(contributionProfileProvider);

    final configToUse =
        profile != null ? engine.blendWithProfile(config, profile) : config;

    final plan = engine.generatePlan(configToUse, contentGen.commitMessages);
    ref.read(appStateProvider.notifier).setPlanSummary(plan);

    widget.onNext();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dateFormat = DateFormat('MMM d, yyyy');

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Behavior Configuration',
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Configure how your fake commits should look - patterns, intensity, and timing.',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 24),

          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Date Range
                  _buildSectionHeader('Date Range', Icons.date_range),
                  Card(
                    child: ListTile(
                      title: Text(
                        '${dateFormat.format(_startDate)} - ${dateFormat.format(_endDate)}',
                      ),
                      subtitle: Text(
                        '${DateRange(_startDate, _endDate).dayCount} days',
                      ),
                      trailing: const Icon(Icons.edit),
                      onTap: _selectDateRange,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Intensity
                  _buildSectionHeader('Average Intensity', Icons.speed),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text('Commits per day (avg)'),
                              Text(
                                _avgIntensity.toStringAsFixed(1),
                                style: theme.textTheme.titleMedium,
                              ),
                            ],
                          ),
                          Slider(
                            value: _avgIntensity,
                            min: 0.5,
                            max: 10.0,
                            divisions: 19,
                            label: _avgIntensity.toStringAsFixed(1),
                            onChanged: (v) => setState(() => _avgIntensity = v),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Weekday Weights
                  _buildSectionHeader(
                      'Weekday Weights', Icons.calendar_view_week),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        children: [
                          for (var day = 1; day <= 7; day++)
                            _buildWeekdaySlider(day),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Sampling & Randomness
                  _buildSectionHeader('Randomness', Icons.shuffle),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Sampling Mode'),
                          const SizedBox(height: 8),
                          SegmentedButton<SamplingMode>(
                            segments: const [
                              ButtonSegment(
                                value: SamplingMode.poisson,
                                label: Text('Poisson'),
                                icon: Icon(Icons.auto_awesome),
                              ),
                              ButtonSegment(
                                value: SamplingMode.normal,
                                label: Text('Normal'),
                                icon: Icon(Icons.equalizer),
                              ),
                            ],
                            selected: {_samplingMode},
                            onSelectionChanged: (v) =>
                                setState(() => _samplingMode = v.first),
                          ),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Min per day: $_minPerDay'),
                                    Slider(
                                      value: _minPerDay.toDouble(),
                                      min: 0,
                                      max: 5,
                                      divisions: 5,
                                      onChanged: (v) => setState(
                                          () => _minPerDay = v.round()),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Max per day: $_maxPerDay'),
                                    Slider(
                                      value: _maxPerDay.toDouble(),
                                      min: 5,
                                      max: 20,
                                      divisions: 15,
                                      onChanged: (v) => setState(
                                          () => _maxPerDay = v.round()),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text('Jitter: +/- $_jitter'),
                          Slider(
                            value: _jitter.toDouble(),
                            min: 0,
                            max: 3,
                            divisions: 3,
                            onChanged: (v) =>
                                setState(() => _jitter = v.round()),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Trend
                  _buildSectionHeader('Trend Over Time', Icons.trending_up),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text('Growth slope'),
                              Text(
                                  '${(_trendSlope * 100).toStringAsFixed(0)}%'),
                            ],
                          ),
                          Slider(
                            value: _trendSlope,
                            min: -0.2,
                            max: 0.3,
                            divisions: 10,
                            onChanged: (v) => setState(() => _trendSlope = v),
                          ),
                          Text(
                            _trendSlope > 0
                                ? 'Commits will gradually increase over time'
                                : _trendSlope < 0
                                    ? 'Commits will gradually decrease over time'
                                    : 'Flat trend (no change over time)',
                            style: theme.textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Holiday Region
                  _buildSectionHeader('Holidays', Icons.celebration),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Skip commits on public holidays from:'),
                          const SizedBox(height: 8),
                          DropdownButtonFormField<HolidayRegion>(
                            initialValue: _holidayRegion,
                            decoration: const InputDecoration(
                              border: OutlineInputBorder(),
                            ),
                            items: HolidayRegion.values.map((r) {
                              return DropdownMenuItem(
                                value: r,
                                child: Text(_regionName(r)),
                              );
                            }).toList(),
                            onChanged: (v) {
                              if (v != null) setState(() => _holidayRegion = v);
                            },
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Holidays will have near-zero commits for natural patterns.',
                            style: theme.textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),

          // Navigation
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              OutlinedButton.icon(
                onPressed: widget.onBack,
                icon: const Icon(Icons.arrow_back),
                label: const Text('Back'),
              ),
              FilledButton.icon(
                onPressed: _proceed,
                icon: const Icon(Icons.arrow_forward),
                label: const Text('Generate Preview'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 20),
          const SizedBox(width: 8),
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildWeekdaySlider(int day) {
    final weight = _weekdayWeights[day] ?? 1.0;
    final names = ['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    final isWeekend = day == 6 || day == 7;

    return Row(
      children: [
        SizedBox(
          width: 40,
          child: Text(
            names[day],
            style: TextStyle(
              fontWeight: isWeekend ? FontWeight.bold : FontWeight.normal,
              color: isWeekend ? Theme.of(context).colorScheme.secondary : null,
            ),
          ),
        ),
        Expanded(
          child: Slider(
            value: weight,
            min: 0,
            max: 1.5,
            divisions: 15,
            onChanged: (v) {
              setState(() => _weekdayWeights[day] = v);
            },
          ),
        ),
        SizedBox(
          width: 50,
          child: Text('${(weight * 100).toStringAsFixed(0)}%'),
        ),
      ],
    );
  }

  String _regionName(HolidayRegion region) {
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
}
