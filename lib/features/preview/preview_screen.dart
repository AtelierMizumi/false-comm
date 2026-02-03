import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../domain/models.dart';
import '../../providers/providers.dart';

class PreviewScreen extends ConsumerStatefulWidget {
  final VoidCallback onNext;
  final VoidCallback onBack;

  const PreviewScreen({
    super.key,
    required this.onNext,
    required this.onBack,
  });

  @override
  ConsumerState<PreviewScreen> createState() => _PreviewScreenState();
}

class _PreviewScreenState extends ConsumerState<PreviewScreen> {
  bool _showTable = false;

  void _regenerate() {
    final behaviorConfig = ref.read(behaviorConfigProvider);
    if (behaviorConfig == null) return;

    final engine = ref.read(behaviorEngineProvider);
    final contentGen = ref.read(contentGeneratorProvider);
    final profile = ref.read(contributionProfileProvider);

    final configToUse = profile != null
        ? engine.blendWithProfile(behaviorConfig, profile)
        : behaviorConfig;

    final plan = engine.generatePlan(configToUse, contentGen.commitMessages);
    ref.read(appStateProvider.notifier).setPlanSummary(plan);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final plan = ref.watch(planSummaryProvider);

    if (plan == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('No plan generated yet'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: widget.onBack,
              child: const Text('Go back to configure'),
            ),
          ],
        ),
      );
    }

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Preview Plan',
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Review the generated commit schedule before execution.',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
              Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    tooltip: 'Regenerate',
                    onPressed: _regenerate,
                  ),
                  const SizedBox(width: 8),
                  SegmentedButton<bool>(
                    segments: const [
                      ButtonSegment(
                        value: false,
                        icon: Icon(Icons.grid_on),
                        label: Text('Heatmap'),
                      ),
                      ButtonSegment(
                        value: true,
                        icon: Icon(Icons.table_rows),
                        label: Text('Table'),
                      ),
                    ],
                    selected: {_showTable},
                    onSelectionChanged: (v) => setState(() => _showTable = v.first),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Summary stats
          _buildSummaryCards(theme, plan),
          const SizedBox(height: 16),

          // Main view
          Expanded(
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: _showTable
                    ? _buildTableView(plan)
                    : _buildHeatmapView(plan),
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Sample commits
          Text('Sample Commits', style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          SizedBox(
            height: 120,
            child: _buildSampleCommits(theme, plan),
          ),
          const SizedBox(height: 16),

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
                onPressed: widget.onNext,
                icon: const Icon(Icons.play_arrow),
                label: const Text('Run'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryCards(ThemeData theme, PlanSummary plan) {
    return Row(
      children: [
        _buildStatCard(
          theme,
          'Total Commits',
          plan.totalCommits.toString(),
          Icons.commit,
        ),
        const SizedBox(width: 12),
        _buildStatCard(
          theme,
          'Active Days',
          '${plan.activeDays}/${plan.totalDays}',
          Icons.calendar_today,
        ),
        const SizedBox(width: 12),
        _buildStatCard(
          theme,
          'Avg/Day',
          plan.averagePerDay.toStringAsFixed(1),
          Icons.analytics,
        ),
        const SizedBox(width: 12),
        _buildStatCard(
          theme,
          'Weekend %',
          '${(plan.weekendRatio * 100).toStringAsFixed(0)}%',
          Icons.weekend,
        ),
        const SizedBox(width: 12),
        _buildStatCard(
          theme,
          'Min-Max',
          '${plan.minPerDay}-${plan.maxPerDay}',
          Icons.unfold_more,
        ),
      ],
    );
  }

  Widget _buildStatCard(
    ThemeData theme,
    String label,
    String value,
    IconData icon,
  ) {
    return Expanded(
      child: Card(
        color: theme.colorScheme.surfaceContainerHighest,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(icon, size: 16, color: theme.colorScheme.primary),
                  const SizedBox(width: 4),
                  Text(
                    label,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                value,
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeatmapView(PlanSummary plan) {
    return ContributionHeatmap(plan: plan);
  }

  Widget _buildTableView(PlanSummary plan) {
    final dateFormat = DateFormat('EEE, MMM d');

    return ListView.builder(
      itemCount: plan.days.length,
      itemBuilder: (context, index) {
        final day = plan.days[index];
        final isWeekend = day.isWeekend;
        final isHoliday = day.isHoliday;

        return ListTile(
          dense: true,
          leading: Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: _getCountColor(day.count),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Center(
              child: Text(
                '${day.count}',
                style: TextStyle(
                  color: day.count > 0 ? Colors.white : Colors.grey,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
          title: Text(dateFormat.format(day.day)),
          subtitle: day.commits.isNotEmpty
              ? Text(
                  day.commits.map((c) => c.message).take(2).join(', '),
                  overflow: TextOverflow.ellipsis,
                )
              : null,
          trailing: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (isHoliday)
                Chip(
                  label: const Text('Holiday'),
                  visualDensity: VisualDensity.compact,
                  backgroundColor: Colors.red.shade100,
                ),
              if (isWeekend && !isHoliday)
                Chip(
                  label: const Text('Weekend'),
                  visualDensity: VisualDensity.compact,
                  backgroundColor: Colors.blue.shade100,
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildSampleCommits(ThemeData theme, PlanSummary plan) {
    final samples = plan.allCommits.take(5).toList();

    if (samples.isEmpty) {
      return const Center(child: Text('No commits in plan'));
    }

    return ListView.builder(
      scrollDirection: Axis.horizontal,
      itemCount: samples.length,
      itemBuilder: (context, index) {
        final commit = samples[index];
        final format = DateFormat('MMM d, HH:mm');

        return Card(
          color: theme.colorScheme.surfaceContainerHighest,
          child: Container(
            width: 200,
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  format.format(commit.timestamp),
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.primary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  commit.message,
                  style: theme.textTheme.bodyMedium,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Color _getCountColor(int count) {
    if (count == 0) return Colors.grey.shade200;
    if (count <= 2) return Colors.green.shade200;
    if (count <= 4) return Colors.green.shade400;
    if (count <= 6) return Colors.green.shade600;
    return Colors.green.shade800;
  }
}

/// GitHub-style contribution heatmap widget
class ContributionHeatmap extends StatelessWidget {
  final PlanSummary plan;

  const ContributionHeatmap({super.key, required this.plan});

  @override
  Widget build(BuildContext context) {
    if (plan.days.isEmpty) {
      return const Center(child: Text('No data to display'));
    }

    // Group days by week
    final weeks = _groupByWeek(plan.days);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Weekday labels
        Row(
          children: [
            const SizedBox(width: 40), // Space for month labels
            ...['Mon', '', 'Wed', '', 'Fri', '', 'Sun']
                .map((d) => SizedBox(
                      width: 14,
                      child: Text(
                        d,
                        style: const TextStyle(fontSize: 9),
                      ),
                    )),
          ],
        ),
        const SizedBox(height: 4),
        Expanded(
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(width: 40),
                ...weeks.map((week) => _buildWeekColumn(week)),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        // Legend
        Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            const Text('Less', style: TextStyle(fontSize: 10)),
            const SizedBox(width: 4),
            _buildLegendBox(Colors.grey.shade200),
            _buildLegendBox(Colors.green.shade200),
            _buildLegendBox(Colors.green.shade400),
            _buildLegendBox(Colors.green.shade600),
            _buildLegendBox(Colors.green.shade800),
            const SizedBox(width: 4),
            const Text('More', style: TextStyle(fontSize: 10)),
          ],
        ),
      ],
    );
  }

  List<List<PlannedDay?>> _groupByWeek(List<PlannedDay> days) {
    if (days.isEmpty) return [];

    final weeks = <List<PlannedDay?>>[];
    var currentWeek = <PlannedDay?>[];

    // Pad the first week with nulls
    final firstDay = days.first.day;
    final startWeekday = firstDay.weekday;
    for (var i = 1; i < startWeekday; i++) {
      currentWeek.add(null);
    }

    for (final day in days) {
      if (currentWeek.length == 7) {
        weeks.add(currentWeek);
        currentWeek = [];
      }
      currentWeek.add(day);
    }

    // Pad the last week
    while (currentWeek.length < 7) {
      currentWeek.add(null);
    }
    if (currentWeek.isNotEmpty) {
      weeks.add(currentWeek);
    }

    return weeks;
  }

  Widget _buildWeekColumn(List<PlannedDay?> week) {
    return Padding(
      padding: const EdgeInsets.only(right: 2),
      child: Column(
        children: week.map((day) => _buildDayCell(day)).toList(),
      ),
    );
  }

  Widget _buildDayCell(PlannedDay? day) {
    final count = day?.count ?? 0;
    final color = _getColor(count);

    return Tooltip(
      message: day != null
          ? '${DateFormat('MMM d').format(day.day)}: $count commits'
          : '',
      child: Container(
        width: 12,
        height: 12,
        margin: const EdgeInsets.all(1),
        decoration: BoxDecoration(
          color: day != null ? color : Colors.transparent,
          borderRadius: BorderRadius.circular(2),
        ),
      ),
    );
  }

  Widget _buildLegendBox(Color color) {
    return Container(
      width: 10,
      height: 10,
      margin: const EdgeInsets.symmetric(horizontal: 1),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(2),
      ),
    );
  }

  Color _getColor(int count) {
    if (count == 0) return Colors.grey.shade200;
    if (count <= 2) return Colors.green.shade200;
    if (count <= 4) return Colors.green.shade400;
    if (count <= 6) return Colors.green.shade600;
    return Colors.green.shade800;
  }
}
