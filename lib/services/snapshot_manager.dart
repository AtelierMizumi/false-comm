import 'dart:convert';
import 'dart:io';
import '../domain/models.dart';
import 'content_generator.dart';
import 'git_adapter.dart';

/// Service for managing run snapshots and undo functionality.
/// Stores snapshots in .fakecomm directory within the repo.
class SnapshotManager {
  static const String _snapshotDir = '.fakecomm';
  static const String _historyFile = 'history.json';

  final String repoPath;

  SnapshotManager(this.repoPath);

  /// Get the full path to the snapshot directory
  String get _snapshotPath => '$repoPath/$_snapshotDir';

  /// Get the full path to the history file
  String get _historyPath => '$_snapshotPath/$_historyFile';

  /// Ensure the snapshot directory exists
  Future<void> _ensureDirectory() async {
    final dir = Directory(_snapshotPath);
    if (!await dir.exists()) {
      await dir.create(recursive: true);
    }

    // Add .gitignore to prevent tracking snapshot files
    final gitignore = File('$_snapshotPath/.gitignore');
    if (!await gitignore.exists()) {
      await gitignore.writeAsString('*\n');
    }
  }

  /// Create a snapshot before running a plan
  Future<RunSnapshot> createSnapshot({
    required PlanSummary plan,
    required String headCommit,
    required String branch,
  }) async {
    await _ensureDirectory();

    final id = _generateSnapshotId();
    final snapshot = RunSnapshot(
      id: id,
      createdAt: DateTime.now(),
      headCommit: headCommit,
      branch: branch,
      filesCreated: [],
      totalCommits: plan.totalCommits,
      pushed: false,
      status: RunStatus.pending,
      repoPath: repoPath,
      plan: plan,
    );

    await _saveSnapshot(snapshot);
    return snapshot;
  }

  /// Update snapshot after execution
  Future<void> updateSnapshot(RunSnapshot snapshot) async {
    await _saveSnapshot(snapshot);
  }

  /// Save a snapshot to file
  Future<void> _saveSnapshot(RunSnapshot snapshot) async {
    await _ensureDirectory();

    final file = File('$_snapshotPath/run-${snapshot.id}.json');
    const encoder = JsonEncoder.withIndent('  ');
    await file.writeAsString(encoder.convert(snapshot.toJson()));

    // Update history index
    await _updateHistoryIndex();
  }

  /// Update the history index file
  Future<void> _updateHistoryIndex() async {
    final snapshots = await loadAllSnapshots();
    final index = snapshots
        .map((s) => {
              'id': s.id,
              'createdAt': s.createdAt.toIso8601String(),
              'totalCommits': s.totalCommits,
              'status': s.status.name,
              'pushed': s.pushed,
            })
        .toList();

    final file = File(_historyPath);
    const encoder = JsonEncoder.withIndent('  ');
    await file.writeAsString(encoder.convert({'runs': index}));
  }

  /// Load all snapshots
  Future<List<RunSnapshot>> loadAllSnapshots() async {
    final dir = Directory(_snapshotPath);
    if (!await dir.exists()) return [];

    final snapshots = <RunSnapshot>[];

    await for (final entity in dir.list()) {
      if (entity is File && entity.path.endsWith('.json')) {
        final filename = entity.path.split(Platform.pathSeparator).last;
        if (filename.startsWith('run-')) {
          try {
            final content = await entity.readAsString();
            final data = json.decode(content) as Map<String, dynamic>;
            snapshots.add(RunSnapshot.fromJson(data));
          } catch (_) {
            // Skip corrupted files
          }
        }
      }
    }

    // Sort by creation time, newest first
    snapshots.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return snapshots;
  }

  /// Load a specific snapshot by ID
  Future<RunSnapshot?> loadSnapshot(String id) async {
    final file = File('$_snapshotPath/run-$id.json');
    if (!await file.exists()) return null;

    try {
      final content = await file.readAsString();
      final data = json.decode(content) as Map<String, dynamic>;
      return RunSnapshot.fromJson(data);
    } catch (_) {
      return null;
    }
  }

  /// Delete a snapshot file
  Future<void> deleteSnapshot(String id) async {
    final file = File('$_snapshotPath/run-$id.json');
    if (await file.exists()) {
      await file.delete();
    }
    await _updateHistoryIndex();
  }

  /// Generate a unique snapshot ID
  String _generateSnapshotId() {
    final now = DateTime.now();
    return '${now.year}${now.month.toString().padLeft(2, '0')}'
        '${now.day.toString().padLeft(2, '0')}-'
        '${now.hour.toString().padLeft(2, '0')}'
        '${now.minute.toString().padLeft(2, '0')}'
        '${now.second.toString().padLeft(2, '0')}-'
        '${now.millisecond.toString().padLeft(3, '0')}';
  }
}

/// Service for undoing a run
class UndoService {
  final GitAdapter git;
  final ContentGeneratorService contentGenerator;
  final SnapshotManager snapshotManager;

  UndoService({
    required this.git,
    required this.contentGenerator,
    required this.snapshotManager,
  });

  /// Undo a run by resetting to snapshot HEAD and cleaning up files
  Future<UndoResult> undoRun(
    RunSnapshot snapshot, {
    bool forcePush = false,
    void Function(String message)? onProgress,
  }) async {
    final errors = <String>[];

    try {
      onProgress?.call('Resetting to previous HEAD...');

      // Reset git to the snapshot's HEAD commit
      final resetResult = await git.resetHard(snapshot.headCommit);
      if (!resetResult.success) {
        return UndoResult(
          success: false,
          errors: ['Failed to reset: ${resetResult.error}'],
        );
      }

      onProgress?.call('Cleaning up created files...');

      // Clean up any files that were created during the run
      await contentGenerator.cleanupFiles(
        snapshot.repoPath,
        snapshot.filesCreated,
      );

      // Update snapshot status
      final updatedSnapshot = snapshot.copyWith(status: RunStatus.undone);
      await snapshotManager.updateSnapshot(updatedSnapshot);

      // Handle force push if needed
      if (snapshot.pushed && forcePush) {
        onProgress?.call('Force pushing to remote...');

        final pushResult = await git.forcePushWithLease();
        if (!pushResult.success) {
          errors.add('Force push failed: ${pushResult.error}');
          errors.add(
              'Remote still has the commits. Manual cleanup may be needed.');
        }
      } else if (snapshot.pushed) {
        errors.add(
            'Commits were pushed to remote. Use force push to remove them.');
      }

      onProgress?.call('Undo complete');

      return UndoResult(
        success: true,
        errors: errors,
        remotePending: snapshot.pushed && !forcePush,
      );
    } catch (e) {
      return UndoResult(
        success: false,
        errors: ['Undo failed: $e'],
      );
    }
  }

  /// Check if undo is safe (no new commits after the run)
  Future<UndoSafetyCheck> checkUndoSafety(RunSnapshot snapshot) async {
    // Get current HEAD
    final currentHead = await git.getHeadCommit();
    if (currentHead == null) {
      return const UndoSafetyCheck(
        isSafe: false,
        reason: 'Could not determine current HEAD',
      );
    }

    // Check if we're on the same branch
    final repoConfig = await git.validateRepo();
    if (repoConfig.branch != snapshot.branch) {
      return UndoSafetyCheck(
        isSafe: false,
        reason:
            'Currently on branch "${repoConfig.branch}" but run was on "${snapshot.branch}"',
      );
    }

    // Check if there are commits after the snapshot
    final commitsBetween = await git.getCommitsBetween(
      snapshot.headCommit,
      currentHead,
    );

    // Expected commits = plan total commits
    final expectedCommits = snapshot.totalCommits;

    if (commitsBetween.length > expectedCommits) {
      return UndoSafetyCheck(
        isSafe: false,
        reason:
            'There are ${commitsBetween.length - expectedCommits} new commits after the run',
        additionalCommits: commitsBetween.length - expectedCommits,
      );
    }

    // Check if dirty
    if (repoConfig.isDirty) {
      return const UndoSafetyCheck(
        isSafe: false,
        reason: 'Repository has uncommitted changes',
      );
    }

    return UndoSafetyCheck(
      isSafe: true,
      willForcePushIfPushed: snapshot.pushed,
    );
  }
}

/// Result of an undo operation
class UndoResult {
  final bool success;
  final List<String> errors;
  final bool remotePending;

  const UndoResult({
    required this.success,
    required this.errors,
    this.remotePending = false,
  });
}

/// Safety check result for undo operation
class UndoSafetyCheck {
  final bool isSafe;
  final String? reason;
  final int additionalCommits;
  final bool willForcePushIfPushed;

  const UndoSafetyCheck({
    required this.isSafe,
    this.reason,
    this.additionalCommits = 0,
    this.willForcePushIfPushed = false,
  });
}
