import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/providers.dart';

class RunScreen extends ConsumerStatefulWidget {
  final VoidCallback onBack;
  final VoidCallback onViewHistory;

  const RunScreen({
    super.key,
    required this.onBack,
    required this.onViewHistory,
  });

  @override
  ConsumerState<RunScreen> createState() => _RunScreenState();
}

class _RunScreenState extends ConsumerState<RunScreen> {
  bool _pushAfter = false;
  bool _confirmed = false;

  void _startExecution() {
    ref.read(executionProvider.notifier).execute(pushAfter: _pushAfter);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final plan = ref.watch(planSummaryProvider);
    final repoConfig = ref.watch(repoConfigProvider);
    final identityConfig = ref.watch(identityConfigProvider);
    final executionState = ref.watch(executionProvider);

    if (plan == null) {
      return const Center(child: Text('No plan to execute'));
    }

    // Show execution in progress
    if (executionState.isRunning) {
      return _buildProgressView(theme, executionState);
    }

    // Show completion
    if (executionState.isComplete) {
      return _buildCompletionView(theme, executionState);
    }

    // Show confirmation
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Execute Plan',
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Review and confirm before creating commits.',
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
                  // Summary card
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Execution Summary',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const Divider(),
                          _buildInfoRow('Repository', repoConfig.path),
                          _buildInfoRow('Branch', repoConfig.branch),
                          _buildInfoRow('Author', '${identityConfig.username} <${identityConfig.email}>'),
                          _buildInfoRow('Total Commits', '${plan.totalCommits}'),
                          _buildInfoRow('Active Days', '${plan.activeDays}'),
                          _buildInfoRow(
                            'Date Range',
                            '${_formatDate(plan.config.dateRange.start)} - ${_formatDate(plan.config.dateRange.end)}',
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Options
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Options',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const Divider(),
                          SwitchListTile(
                            contentPadding: EdgeInsets.zero,
                            title: const Text('Push to remote after completion'),
                            subtitle: Text(
                              repoConfig.remoteUrl ?? 'No remote configured',
                              style: theme.textTheme.bodySmall,
                            ),
                            value: _pushAfter,
                            onChanged: repoConfig.remoteUrl != null
                                ? (v) => setState(() => _pushAfter = v)
                                : null,
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Warning
                  Card(
                    color: theme.colorScheme.tertiaryContainer,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Icon(
                            Icons.warning,
                            color: theme.colorScheme.onTertiaryContainer,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              'This will create ${plan.totalCommits} real Git commits in your repository. '
                              'A snapshot will be saved to allow undo.',
                              style: TextStyle(
                                color: theme.colorScheme.onTertiaryContainer,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Confirmation checkbox
                  CheckboxListTile(
                    value: _confirmed,
                    onChanged: (v) => setState(() => _confirmed = v ?? false),
                    title: const Text('I understand this will modify my repository'),
                    subtitle: const Text('Commits can be undone using the history feature'),
                    controlAffinity: ListTileControlAffinity.leading,
                  ),
                ],
              ),
            ),
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
                onPressed: _confirmed ? _startExecution : null,
                icon: const Icon(Icons.play_arrow),
                label: const Text('Execute Plan'),
                style: FilledButton.styleFrom(
                  backgroundColor: _confirmed
                      ? theme.colorScheme.primary
                      : theme.colorScheme.outline,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildProgressView(ThemeData theme, ExecutionState state) {
    return Center(
      child: Card(
        child: Container(
          width: 400,
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 24),
              Text(
                'Executing Plan...',
                style: theme.textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              LinearProgressIndicator(
                value: state.progress,
              ),
              const SizedBox(height: 8),
              Text(
                'Commit ${state.currentCommit} of ${state.totalCommits}',
                style: theme.textTheme.bodyMedium,
              ),
              if (state.currentMessage != null) ...[
                const SizedBox(height: 8),
                Text(
                  state.currentMessage!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCompletionView(ThemeData theme, ExecutionState state) {
    final result = state.result;
    final isSuccess = result?.isSuccess ?? false;

    return Center(
      child: Card(
        child: Container(
          width: 450,
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                isSuccess ? Icons.check_circle : Icons.error,
                size: 64,
                color: isSuccess
                    ? theme.colorScheme.primary
                    : theme.colorScheme.error,
              ),
              const SizedBox(height: 16),
              Text(
                isSuccess ? 'Execution Complete!' : 'Execution Failed',
                style: theme.textTheme.titleLarge,
              ),
              const SizedBox(height: 16),
              if (result != null) ...[
                _buildResultRow('Commits Created', '${result.successCount}'),
                if (result.failCount > 0)
                  _buildResultRow('Failed', '${result.failCount}'),
                _buildResultRow('Files Created', '${result.filesCreated.length}'),
                _buildResultRow('Pushed', result.pushed ? 'Yes' : 'No'),
                if (result.pushError != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      'Push error: ${result.pushError}',
                      style: TextStyle(color: theme.colorScheme.error),
                    ),
                  ),
              ],
              if (state.error != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    state.error!,
                    style: TextStyle(color: theme.colorScheme.error),
                  ),
                ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  OutlinedButton(
                    onPressed: () {
                      ref.read(executionProvider.notifier).reset();
                    },
                    child: const Text('Run Again'),
                  ),
                  const SizedBox(width: 16),
                  FilledButton.icon(
                    onPressed: widget.onViewHistory,
                    icon: const Icon(Icons.history),
                    label: const Text('View History'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(
            child: Text(value),
          ),
        ],
      ),
    );
  }

  Widget _buildResultRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text('$label: ', style: const TextStyle(fontWeight: FontWeight.w500)),
          Text(value),
        ],
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }
}
