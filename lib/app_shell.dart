import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'domain/models.dart';
import 'providers/providers.dart';
import 'features/repo_picker/repo_picker_screen.dart';
import 'features/identity/identity_screen.dart';
import 'features/behavior_config/behavior_config_screen.dart';
import 'features/preview/preview_screen.dart';
import 'features/run/run_screen.dart';
import 'features/history/history_screen.dart';

class AppShell extends ConsumerStatefulWidget {
  const AppShell({super.key});

  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _AppShellState extends ConsumerState<AppShell> {
  int _currentIndex = 0;
  bool _showHistory = false;

  final _stepLabels = const [
    'Repository',
    'Identity',
    'Behavior',
    'Preview',
    'Execute',
  ];

  final _stepIcons = const [
    Icons.folder,
    Icons.person,
    Icons.tune,
    Icons.preview,
    Icons.play_arrow,
  ];

  void _goToStep(int index) {
    setState(() {
      _currentIndex = index;
      _showHistory = false;
    });
    ref.read(appStateProvider.notifier).goToStep(AppStep.values[index]);
  }

  void _nextStep() {
    if (_currentIndex < _stepLabels.length - 1) {
      _goToStep(_currentIndex + 1);
    }
  }

  void _prevStep() {
    if (_currentIndex > 0) {
      _goToStep(_currentIndex - 1);
    }
  }

  void _showHistoryScreen() {
    setState(() => _showHistory = true);
  }

  void _hideHistoryScreen() {
    setState(() => _showHistory = false);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: Row(
        children: [
          // Side navigation rail
          Container(
            width: 220,
            color: theme.colorScheme.surfaceContainerHighest,
            child: Column(
              children: [
                // App header
                Container(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Icon(
                        Icons.commit,
                        size: 32,
                        color: theme.colorScheme.primary,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'FakeComm',
                              style: theme.textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Text(
                              'Commit Planner',
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: theme.colorScheme.onSurfaceVariant,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const Divider(),

                // Stepper
                Expanded(
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    itemCount: _stepLabels.length,
                    itemBuilder: (context, index) {
                      return _buildStepTile(
                        context,
                        index,
                        _stepLabels[index],
                        _stepIcons[index],
                      );
                    },
                  ),
                ),

                const Divider(),

                // History button
                ListTile(
                  leading: Icon(
                    Icons.history,
                    color: _showHistory
                        ? theme.colorScheme.primary
                        : theme.colorScheme.onSurfaceVariant,
                  ),
                  title: Text(
                    'Run History',
                    style: TextStyle(
                      color: _showHistory
                          ? theme.colorScheme.primary
                          : theme.colorScheme.onSurfaceVariant,
                      fontWeight:
                          _showHistory ? FontWeight.bold : FontWeight.normal,
                    ),
                  ),
                  selected: _showHistory,
                  onTap: _showHistoryScreen,
                ),
                const SizedBox(height: 8),
              ],
            ),
          ),

          // Main content
          Expanded(
            child: _showHistory
                ? HistoryScreen(onBack: _hideHistoryScreen)
                : _buildCurrentScreen(),
          ),
        ],
      ),
    );
  }

  Widget _buildStepTile(
    BuildContext context,
    int index,
    String label,
    IconData icon,
  ) {
    final theme = Theme.of(context);
    final isActive = index == _currentIndex && !_showHistory;
    final isCompleted = _isStepCompleted(index);
    final isEnabled = _isStepEnabled(index);

    Color getColor() {
      if (isActive) return theme.colorScheme.primary;
      if (isCompleted) return Color.alphaBlend(theme.colorScheme.primary.withAlpha(180), Colors.white);
      if (!isEnabled) return Color.alphaBlend(theme.colorScheme.outline.withAlpha(128), Colors.white);
      return theme.colorScheme.onSurfaceVariant;
    }

    return ListTile(
      leading: Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: isActive
              ? theme.colorScheme.primaryContainer
              : isCompleted
                  ? Color.alphaBlend(theme.colorScheme.primaryContainer.withAlpha(128), Colors.white)
                  : Colors.transparent,
          border: Border.all(
            color: getColor(),
            width: isActive ? 2 : 1,
          ),
        ),
        child: Center(
          child: isCompleted && !isActive
              ? Icon(Icons.check, size: 16, color: getColor())
              : Text(
                  '${index + 1}',
                  style: TextStyle(
                    color: getColor(),
                    fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
        ),
      ),
      title: Text(
        label,
        style: TextStyle(
          color: getColor(),
          fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
        ),
      ),
      selected: isActive,
      enabled: isEnabled,
      onTap: isEnabled ? () => _goToStep(index) : null,
    );
  }

  bool _isStepCompleted(int index) {
    final state = ref.read(appStateProvider);
    switch (index) {
      case 0:
        return state.repoConfig.isValid;
      case 1:
        return state.identityConfig.username.isNotEmpty;
      case 2:
        return state.behaviorConfig != null;
      case 3:
        return state.planSummary != null;
      case 4:
        return state.runHistory.isNotEmpty;
      default:
        return false;
    }
  }

  bool _isStepEnabled(int index) {
    // Step 0 is always enabled
    if (index == 0) return true;

    // Other steps require previous step to be completed
    return _isStepCompleted(index - 1);
  }

  Widget _buildCurrentScreen() {
    switch (_currentIndex) {
      case 0:
        return RepoPickerScreen(onNext: _nextStep);
      case 1:
        return IdentityScreen(onNext: _nextStep, onBack: _prevStep);
      case 2:
        return BehaviorConfigScreen(onNext: _nextStep, onBack: _prevStep);
      case 3:
        return PreviewScreen(onNext: _nextStep, onBack: _prevStep);
      case 4:
        return RunScreen(onBack: _prevStep, onViewHistory: _showHistoryScreen);
      default:
        return const Center(child: Text('Unknown step'));
    }
  }
}
