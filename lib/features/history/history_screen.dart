import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../domain/models.dart';
import '../../providers/providers.dart';
import '../../services/snapshot_manager.dart';

class HistoryScreen extends ConsumerStatefulWidget {
  final VoidCallback onBack;

  const HistoryScreen({super.key, required this.onBack});

  @override
  ConsumerState<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends ConsumerState<HistoryScreen> {
  bool _isLoading = false;
  RunSnapshot? _selectedSnapshot;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final repoConfig = ref.read(repoConfigProvider);
    if (!repoConfig.isValid) return;

    setState(() => _isLoading = true);

    try {
      final manager = SnapshotManager(repoConfig.path);
      final snapshots = await manager.loadAllSnapshots();
      ref.read(appStateProvider.notifier).setRunHistory(snapshots);
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _showUndoDialog(RunSnapshot snapshot) {
    showDialog(
      context: context,
      builder: (context) => _UndoConfirmDialog(
        snapshot: snapshot,
        onConfirm: (forcePush) => _performUndo(snapshot, forcePush),
      ),
    );
  }

  Future<void> _performUndo(RunSnapshot snapshot, bool forcePush) async {
    Navigator.of(context).pop(); // Close dialog

    // Check safety first
    await ref.read(undoProvider.notifier).checkSafety(snapshot);
    final safetyCheck = ref.read(undoProvider).safetyCheck;

    if (safetyCheck != null && !safetyCheck.isSafe) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Cannot undo: ${safetyCheck.reason}'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
      return;
    }

    // Perform undo
    await ref.read(undoProvider.notifier).performUndo(snapshot, forcePush: forcePush);
    final result = ref.read(undoProvider).result;

    if (mounted) {
      if (result?.success == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Undo completed successfully')),
        );
        _loadHistory(); // Refresh
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Undo failed: ${result?.errors.join(', ') ?? 'Unknown error'}'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    }

    ref.read(undoProvider.notifier).reset();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final history = ref.watch(runHistoryProvider);
    final undoState = ref.watch(undoProvider);

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
                    'Run History',
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'View past runs and undo if needed.',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
              IconButton(
                icon: const Icon(Icons.refresh),
                tooltip: 'Refresh',
                onPressed: _loadHistory,
              ),
            ],
          ),
          const SizedBox(height: 24),

          if (_isLoading || undoState.isProcessing)
            const Center(child: CircularProgressIndicator())
          else if (history.isEmpty)
            Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.history,
                      size: 64,
                      color: theme.colorScheme.outline,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'No run history yet',
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: theme.colorScheme.outline,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Completed runs will appear here',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.outline,
                      ),
                    ),
                  ],
                ),
              ),
            )
          else
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // List
                  Expanded(
                    flex: 2,
                    child: Card(
                      child: ListView.separated(
                        itemCount: history.length,
                        separatorBuilder: (_, __) => const Divider(height: 1),
                        itemBuilder: (context, index) {
                          final snapshot = history[index];
                          final isSelected = _selectedSnapshot?.id == snapshot.id;

                          return _buildSnapshotTile(
                            theme,
                            snapshot,
                            isSelected,
                            () => setState(() => _selectedSnapshot = snapshot),
                          );
                        },
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  // Details
                  Expanded(
                    flex: 3,
                    child: _selectedSnapshot != null
                        ? _buildSnapshotDetails(theme, _selectedSnapshot!)
                        : Card(
                            child: Center(
                              child: Text(
                                'Select a run to view details',
                                style: theme.textTheme.bodyMedium?.copyWith(
                                  color: theme.colorScheme.outline,
                                ),
                              ),
                            ),
                          ),
                  ),
                ],
              ),
            ),

          const SizedBox(height: 16),

          // Navigation
          Row(
            mainAxisAlignment: MainAxisAlignment.start,
            children: [
              OutlinedButton.icon(
                onPressed: widget.onBack,
                icon: const Icon(Icons.arrow_back),
                label: const Text('Back to Planner'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSnapshotTile(
    ThemeData theme,
    RunSnapshot snapshot,
    bool isSelected,
    VoidCallback onTap,
  ) {
    final dateFormat = DateFormat('MMM d, yyyy HH:mm');

    return ListTile(
      selected: isSelected,
      selectedTileColor: theme.colorScheme.primaryContainer,
      onTap: onTap,
      leading: Icon(
        _getStatusIcon(snapshot.status),
        color: _getStatusColor(snapshot.status),
      ),
      title: Text(dateFormat.format(snapshot.createdAt)),
      subtitle: Text('${snapshot.totalCommits} commits'),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (snapshot.pushed)
            Tooltip(
              message: 'Pushed to remote',
              child: Icon(
                Icons.cloud_upload,
                size: 18,
                color: theme.colorScheme.primary,
              ),
            ),
          const SizedBox(width: 4),
          Chip(
            label: Text(
              _statusLabel(snapshot.status),
              style: TextStyle(
                fontSize: 11,
                color: _getStatusColor(snapshot.status),
              ),
            ),
            visualDensity: VisualDensity.compact,
            padding: EdgeInsets.zero,
          ),
        ],
      ),
    );
  }

  Widget _buildSnapshotDetails(ThemeData theme, RunSnapshot snapshot) {
    final dateFormat = DateFormat('MMM d, yyyy HH:mm:ss');
    final canUndo = snapshot.status == RunStatus.completed;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Run Details',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (canUndo)
                  FilledButton.tonalIcon(
                    onPressed: () => _showUndoDialog(snapshot),
                    icon: const Icon(Icons.undo),
                    label: const Text('Undo Run'),
                  ),
              ],
            ),
            const Divider(),
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildDetailRow('ID', snapshot.id),
                    _buildDetailRow('Created', dateFormat.format(snapshot.createdAt)),
                    _buildDetailRow('Status', _statusLabel(snapshot.status)),
                    _buildDetailRow('Branch', snapshot.branch),
                    _buildDetailRow('Total Commits', '${snapshot.totalCommits}'),
                    _buildDetailRow('Pushed', snapshot.pushed ? 'Yes' : 'No'),
                    _buildDetailRow('Head Commit (before)', snapshot.headCommit),
                    const SizedBox(height: 16),
                    Text(
                      'Files Created (${snapshot.filesCreated.length})',
                      style: theme.textTheme.titleSmall,
                    ),
                    const SizedBox(height: 8),
                    if (snapshot.filesCreated.isEmpty)
                      Text(
                        'No files recorded',
                        style: theme.textTheme.bodySmall,
                      )
                    else
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: snapshot.filesCreated
                              .take(20)
                              .map((f) => Text(
                                    f,
                                    style: theme.textTheme.bodySmall?.copyWith(
                                      fontFamily: 'monospace',
                                    ),
                                  ))
                              .toList(),
                        ),
                      ),
                    if (snapshot.filesCreated.length > 20)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                          '... and ${snapshot.filesCreated.length - 20} more',
                          style: theme.textTheme.bodySmall,
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(
            child: SelectableText(value),
          ),
        ],
      ),
    );
  }

  IconData _getStatusIcon(RunStatus status) {
    switch (status) {
      case RunStatus.pending:
        return Icons.hourglass_empty;
      case RunStatus.running:
        return Icons.play_circle;
      case RunStatus.completed:
        return Icons.check_circle;
      case RunStatus.failed:
        return Icons.error;
      case RunStatus.undone:
        return Icons.undo;
    }
  }

  Color _getStatusColor(RunStatus status) {
    switch (status) {
      case RunStatus.pending:
        return Colors.grey;
      case RunStatus.running:
        return Colors.blue;
      case RunStatus.completed:
        return Colors.green;
      case RunStatus.failed:
        return Colors.red;
      case RunStatus.undone:
        return Colors.orange;
    }
  }

  String _statusLabel(RunStatus status) {
    switch (status) {
      case RunStatus.pending:
        return 'Pending';
      case RunStatus.running:
        return 'Running';
      case RunStatus.completed:
        return 'Completed';
      case RunStatus.failed:
        return 'Failed';
      case RunStatus.undone:
        return 'Undone';
    }
  }
}

class _UndoConfirmDialog extends StatefulWidget {
  final RunSnapshot snapshot;
  final void Function(bool forcePush) onConfirm;

  const _UndoConfirmDialog({
    required this.snapshot,
    required this.onConfirm,
  });

  @override
  State<_UndoConfirmDialog> createState() => _UndoConfirmDialogState();
}

class _UndoConfirmDialogState extends State<_UndoConfirmDialog> {
  bool _forcePush = true;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AlertDialog(
      title: const Row(
        children: [
          Icon(Icons.warning, color: Colors.orange),
          SizedBox(width: 8),
          Text('Confirm Undo'),
        ],
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'This will reset your repository to the state before this run.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          Text(
            'The following will happen:',
            style: theme.textTheme.titleSmall,
          ),
          const SizedBox(height: 8),
          const Text('- Git will be reset to the previous HEAD commit'),
          const Text('- Created files will be cleaned up'),
          if (widget.snapshot.pushed) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: theme.colorScheme.errorContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.cloud_upload, color: theme.colorScheme.error),
                      const SizedBox(width: 8),
                      Text(
                        'These commits were pushed!',
                        style: TextStyle(
                          color: theme.colorScheme.onErrorContainer,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    value: _forcePush,
                    onChanged: (v) => setState(() => _forcePush = v),
                    title: const Text('Force push to remove remote commits'),
                    subtitle: const Text(
                      'Uses --force-with-lease for safety',
                      style: TextStyle(fontSize: 12),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () => widget.onConfirm(_forcePush),
          style: FilledButton.styleFrom(
            backgroundColor: theme.colorScheme.error,
          ),
          child: const Text('Undo Run'),
        ),
      ],
    );
  }
}
