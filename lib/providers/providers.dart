import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../domain/models.dart';
import '../services/services.dart';

// ============================================================================
// SERVICE PROVIDERS
// ============================================================================

/// Holiday service provider
final holidayServiceProvider = Provider<HolidayService>((ref) {
  return const HolidayService();
});

/// Behavior engine provider
final behaviorEngineProvider = Provider<BehaviorEngine>((ref) {
  return BehaviorEngine();
});

/// Content generator provider
final contentGeneratorProvider = Provider<ContentGeneratorService>((ref) {
  return ContentGeneratorService();
});

/// GitHub history service provider
final githubHistoryServiceProvider = Provider<GitHubHistoryService>((ref) {
  return GitHubHistoryService();
});

// ============================================================================
// STATE NOTIFIERS
// ============================================================================

/// Main app state notifier
class AppStateNotifier extends StateNotifier<AppState> {
  final Ref ref;

  AppStateNotifier(this.ref) : super(const AppState());

  /// Navigate to a specific step
  void goToStep(AppStep step) {
    state = state.copyWith(currentStep: step);
  }

  /// Set repo configuration
  void setRepoConfig(RepoConfig config) {
    state = state.copyWith(repoConfig: config);
  }

  /// Set identity configuration
  void setIdentityConfig(IdentityConfig config) {
    state = state.copyWith(identityConfig: config);
  }

  /// Set behavior configuration
  void setBehaviorConfig(BehaviorConfig config) {
    state = state.copyWith(behaviorConfig: config);
  }

  /// Set the generated plan summary
  void setPlanSummary(PlanSummary summary) {
    state = state.copyWith(planSummary: summary);
  }

  /// Set run history
  void setRunHistory(List<RunSnapshot> history) {
    state = state.copyWith(runHistory: history);
  }

  /// Add a run to history
  void addRunToHistory(RunSnapshot run) {
    state = state.copyWith(runHistory: [run, ...state.runHistory]);
  }

  /// Update a run in history
  void updateRunInHistory(RunSnapshot run) {
    final updated = state.runHistory.map((r) {
      return r.id == run.id ? run : r;
    }).toList();
    state = state.copyWith(runHistory: updated);
  }

  /// Set running state
  void setRunning(bool running) {
    state = state.copyWith(isRunning: running);
  }

  /// Set error message
  void setError(String? error) {
    state = state.copyWith(errorMessage: error);
  }

  /// Set contribution profile
  void setContributionProfile(ContributionProfile? profile) {
    state = state.copyWith(contributionProfile: profile);
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(errorMessage: null);
  }

  /// Reset to initial state
  void reset() {
    state = const AppState();
  }
}

/// App state provider
final appStateProvider =
    StateNotifierProvider<AppStateNotifier, AppState>((ref) {
  return AppStateNotifier(ref);
});

// ============================================================================
// COMPUTED PROVIDERS
// ============================================================================

/// Current step provider
final currentStepProvider = Provider<AppStep>((ref) {
  return ref.watch(appStateProvider).currentStep;
});

/// Repo config provider
final repoConfigProvider = Provider<RepoConfig>((ref) {
  return ref.watch(appStateProvider).repoConfig;
});

/// Identity config provider
final identityConfigProvider = Provider<IdentityConfig>((ref) {
  return ref.watch(appStateProvider).identityConfig;
});

/// Behavior config provider
final behaviorConfigProvider = Provider<BehaviorConfig?>((ref) {
  return ref.watch(appStateProvider).behaviorConfig;
});

/// Plan summary provider
final planSummaryProvider = Provider<PlanSummary?>((ref) {
  return ref.watch(appStateProvider).planSummary;
});

/// Run history provider
final runHistoryProvider = Provider<List<RunSnapshot>>((ref) {
  return ref.watch(appStateProvider).runHistory;
});

/// Is running provider
final isRunningProvider = Provider<bool>((ref) {
  return ref.watch(appStateProvider).isRunning;
});

/// Contribution profile provider
final contributionProfileProvider = Provider<ContributionProfile?>((ref) {
  return ref.watch(appStateProvider).contributionProfile;
});

// ============================================================================
// ACTION PROVIDERS
// ============================================================================

/// Validate repository
final validateRepoProvider =
    FutureProvider.family<RepoConfig, String>((ref, path) async {
  final git = GitAdapter(path);
  return git.validateRepo();
});

/// Generate plan preview
final generatePlanProvider = Provider<PlanSummary? Function()>((ref) {
  return () {
    final behaviorConfig = ref.read(behaviorConfigProvider);
    if (behaviorConfig == null) return null;

    final engine = ref.read(behaviorEngineProvider);
    final contentGen = ref.read(contentGeneratorProvider);

    // Optionally blend with contribution profile
    final profile = ref.read(contributionProfileProvider);
    final configToUse = profile != null
        ? engine.blendWithProfile(behaviorConfig, profile)
        : behaviorConfig;

    return engine.generatePlan(configToUse, contentGen.commitMessages);
  };
});

/// Fetch GitHub contributions
final fetchContributionsProvider = FutureProvider.family<ContributionProfile?,
    ({String username, String? pat})>(
  (ref, params) async {
    final service = ref.read(githubHistoryServiceProvider);
    return service.fetchProfile(params.username, pat: params.pat);
  },
);

/// Get holidays for region and date range
final holidaysForConfigProvider = Provider<List<DateTime>>((ref) {
  final behaviorConfig = ref.watch(behaviorConfigProvider);
  if (behaviorConfig == null) return [];

  final holidayService = ref.read(holidayServiceProvider);
  return holidayService.getHolidays(
    behaviorConfig.holidayRegion,
    behaviorConfig.dateRange,
  );
});

// ============================================================================
// EXECUTION PROVIDER
// ============================================================================

/// Execution state for tracking progress
class ExecutionState {
  final bool isRunning;
  final int currentCommit;
  final int totalCommits;
  final String? currentMessage;
  final bool isComplete;
  final ExecutionResult? result;
  final String? error;

  const ExecutionState({
    this.isRunning = false,
    this.currentCommit = 0,
    this.totalCommits = 0,
    this.currentMessage,
    this.isComplete = false,
    this.result,
    this.error,
  });

  ExecutionState copyWith({
    bool? isRunning,
    int? currentCommit,
    int? totalCommits,
    String? currentMessage,
    bool? isComplete,
    ExecutionResult? result,
    String? error,
  }) {
    return ExecutionState(
      isRunning: isRunning ?? this.isRunning,
      currentCommit: currentCommit ?? this.currentCommit,
      totalCommits: totalCommits ?? this.totalCommits,
      currentMessage: currentMessage,
      isComplete: isComplete ?? this.isComplete,
      result: result ?? this.result,
      error: error,
    );
  }

  double get progress => totalCommits > 0 ? currentCommit / totalCommits : 0;
}

class ExecutionNotifier extends StateNotifier<ExecutionState> {
  final Ref ref;

  ExecutionNotifier(this.ref) : super(const ExecutionState());

  Future<void> execute({
    required bool pushAfter,
  }) async {
    final appState = ref.read(appStateProvider);
    final plan = appState.planSummary;
    final repoConfig = appState.repoConfig;
    final identityConfig = appState.identityConfig;

    if (plan == null || !repoConfig.isValid) {
      state = state.copyWith(error: 'Invalid configuration');
      return;
    }

    state = ExecutionState(
      isRunning: true,
      totalCommits: plan.totalCommits,
    );

    try {
      final git = GitAdapter(repoConfig.path);
      final contentGen = ref.read(contentGeneratorProvider);
      final snapshotManager = SnapshotManager(repoConfig.path);

      // Get current HEAD for snapshot
      final headCommit = await git.getHeadCommit();
      if (headCommit == null) {
        state = state.copyWith(
          isRunning: false,
          error: 'Could not get current HEAD commit',
        );
        return;
      }

      // Create snapshot
      var snapshot = await snapshotManager.createSnapshot(
        plan: plan,
        headCommit: headCommit,
        branch: repoConfig.branch,
      );

      // Update snapshot to running
      snapshot = snapshot.copyWith(status: RunStatus.running);
      await snapshotManager.updateSnapshot(snapshot);

      // Execute
      final executionService = ExecutionService(
        git: git,
        onProgress: (current, total, message) {
          state = state.copyWith(
            currentCommit: current,
            totalCommits: total,
            currentMessage: message,
          );
        },
      );

      final result = await executionService.executePlan(
        plan: plan,
        contentGenerator: contentGen,
        authorName: identityConfig.username,
        authorEmail: identityConfig.email,
        pushAfter: pushAfter,
      );

      // Update snapshot with result
      snapshot = snapshot.copyWith(
        filesCreated: result.filesCreated,
        totalCommits: result.successCount,
        pushed: result.pushed,
        status: result.isSuccess ? RunStatus.completed : RunStatus.failed,
      );
      await snapshotManager.updateSnapshot(snapshot);

      // Add to history
      ref.read(appStateProvider.notifier).addRunToHistory(snapshot);

      state = ExecutionState(
        isRunning: false,
        isComplete: true,
        result: result,
        currentCommit: result.totalCommits,
        totalCommits: result.totalCommits,
      );
    } catch (e) {
      state = state.copyWith(
        isRunning: false,
        error: e.toString(),
      );
    }
  }

  void reset() {
    state = const ExecutionState();
  }
}

final executionProvider =
    StateNotifierProvider<ExecutionNotifier, ExecutionState>((ref) {
  return ExecutionNotifier(ref);
});

// ============================================================================
// UNDO PROVIDER
// ============================================================================

class UndoState {
  final bool isProcessing;
  final UndoSafetyCheck? safetyCheck;
  final UndoResult? result;
  final String? error;

  const UndoState({
    this.isProcessing = false,
    this.safetyCheck,
    this.result,
    this.error,
  });

  UndoState copyWith({
    bool? isProcessing,
    UndoSafetyCheck? safetyCheck,
    UndoResult? result,
    String? error,
  }) {
    return UndoState(
      isProcessing: isProcessing ?? this.isProcessing,
      safetyCheck: safetyCheck ?? this.safetyCheck,
      result: result ?? this.result,
      error: error,
    );
  }
}

class UndoNotifier extends StateNotifier<UndoState> {
  final Ref ref;

  UndoNotifier(this.ref) : super(const UndoState());

  Future<void> checkSafety(RunSnapshot snapshot) async {
    state = state.copyWith(isProcessing: true);

    try {
      final git = GitAdapter(snapshot.repoPath);
      final contentGen = ref.read(contentGeneratorProvider);
      final snapshotManager = SnapshotManager(snapshot.repoPath);

      final undoService = UndoService(
        git: git,
        contentGenerator: contentGen,
        snapshotManager: snapshotManager,
      );

      final check = await undoService.checkUndoSafety(snapshot);
      state = UndoState(safetyCheck: check);
    } catch (e) {
      state = UndoState(error: e.toString());
    }
  }

  Future<void> performUndo(RunSnapshot snapshot,
      {bool forcePush = false}) async {
    state = state.copyWith(isProcessing: true);

    try {
      final git = GitAdapter(snapshot.repoPath);
      final contentGen = ref.read(contentGeneratorProvider);
      final snapshotManager = SnapshotManager(snapshot.repoPath);

      final undoService = UndoService(
        git: git,
        contentGenerator: contentGen,
        snapshotManager: snapshotManager,
      );

      final result = await undoService.undoRun(snapshot, forcePush: forcePush);
      state = UndoState(result: result);

      if (result.success) {
        // Update the run in history
        final updatedSnapshot = snapshot.copyWith(status: RunStatus.undone);
        ref.read(appStateProvider.notifier).updateRunInHistory(updatedSnapshot);
      }
    } catch (e) {
      state = UndoState(error: e.toString());
    }
  }

  void reset() {
    state = const UndoState();
  }
}

final undoProvider = StateNotifierProvider<UndoNotifier, UndoState>((ref) {
  return UndoNotifier(ref);
});
