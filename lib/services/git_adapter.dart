import 'dart:convert';
import 'dart:io';
import '../domain/models.dart';

/// Result of a git operation
class GitResult {
  final bool success;
  final String output;
  final String? error;
  final int exitCode;

  const GitResult({
    required this.success,
    required this.output,
    this.error,
    required this.exitCode,
  });
}

/// Adapter for executing Git commands
class GitAdapter {
  final String repoPath;

  GitAdapter(this.repoPath);

  /// Check if git is available and get version
  static Future<String?> getGitVersion() async {
    try {
      final result = await Process.run('git', ['--version']);
      if (result.exitCode == 0) {
        return (result.stdout as String).trim();
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  /// Validate that a path is a git repository
  Future<RepoConfig> validateRepo() async {
    final path = repoPath;

    // Check if directory exists
    final dir = Directory(path);
    if (!await dir.exists()) {
      return RepoConfig(path: path, branch: '', isValid: false);
    }

    // Check if it's a git repo
    final gitDir = Directory('$path/.git');
    if (!await gitDir.exists()) {
      return RepoConfig(path: path, branch: '', isValid: false);
    }

    // Get git version
    final gitVersion = await getGitVersion();
    if (gitVersion == null) {
      return RepoConfig(path: path, branch: '', isValid: false);
    }

    // Get current branch
    final branchResult = await _run(['rev-parse', '--abbrev-ref', 'HEAD']);
    final branch = branchResult.success ? branchResult.output.trim() : 'main';

    // Check if dirty
    final statusResult = await _run(['status', '--porcelain']);
    final isDirty =
        statusResult.success && statusResult.output.trim().isNotEmpty;

    // Get remote URL
    final remoteResult = await _run(['config', '--get', 'remote.origin.url']);
    final remoteUrl = remoteResult.success ? remoteResult.output.trim() : null;

    return RepoConfig(
      path: path,
      branch: branch,
      isValid: true,
      gitVersion: gitVersion,
      isDirty: isDirty,
      remoteUrl: remoteUrl,
    );
  }

  /// Get current HEAD commit SHA
  Future<String?> getHeadCommit() async {
    final result = await _run(['rev-parse', 'HEAD']);
    return result.success ? result.output.trim() : null;
  }

  /// Get configured user email
  Future<String?> getConfiguredEmail() async {
    final result = await _run(['config', 'user.email']);
    return result.success ? result.output.trim() : null;
  }

  /// Get configured user name
  Future<String?> getConfiguredName() async {
    final result = await _run(['config', 'user.name']);
    return result.success ? result.output.trim() : null;
  }

  /// Set local user email for this repo
  Future<bool> setLocalEmail(String email) async {
    final result = await _run(['config', 'user.email', email]);
    return result.success;
  }

  /// Set local user name for this repo
  Future<bool> setLocalName(String name) async {
    final result = await _run(['config', 'user.name', name]);
    return result.success;
  }

  /// Create a commit with specific author and committer dates
  Future<GitResult> createCommit({
    required String message,
    required DateTime timestamp,
    String? authorName,
    String? authorEmail,
  }) async {
    // Format timestamp for git (ISO 8601)
    final dateString = _formatGitDate(timestamp);

    // Build environment with date overrides
    final env = Map<String, String>.from(Platform.environment);
    env['GIT_AUTHOR_DATE'] = dateString;
    env['GIT_COMMITTER_DATE'] = dateString;

    if (authorName != null) {
      env['GIT_AUTHOR_NAME'] = authorName;
      env['GIT_COMMITTER_NAME'] = authorName;
    }
    if (authorEmail != null) {
      env['GIT_AUTHOR_EMAIL'] = authorEmail;
      env['GIT_COMMITTER_EMAIL'] = authorEmail;
    }

    return _run(['commit', '-m', message], environment: env);
  }

  /// Stage files for commit
  Future<GitResult> add(List<String> files) async {
    return _run(['add', ...files]);
  }

  /// Stage all changes
  Future<GitResult> addAll() async {
    return _run(['add', '-A']);
  }

  /// Push to remote
  Future<GitResult> push({String? remote, String? branch}) async {
    final args = ['push'];
    if (remote != null) args.add(remote);
    if (branch != null) args.add(branch);
    return _run(args);
  }

  /// Force push with lease (safer force push)
  Future<GitResult> forcePushWithLease({String? remote, String? branch}) async {
    final args = ['push', '--force-with-lease'];
    if (remote != null) args.add(remote);
    if (branch != null) args.add(branch);
    return _run(args);
  }

  /// Reset to a specific commit
  Future<GitResult> resetHard(String commitSha) async {
    return _run(['reset', '--hard', commitSha]);
  }

  /// Reset to a specific commit (soft - keep changes staged)
  Future<GitResult> resetSoft(String commitSha) async {
    return _run(['reset', '--soft', commitSha]);
  }

  /// Get list of commits between two refs
  Future<List<String>> getCommitsBetween(String fromRef, String toRef) async {
    final result = await _run(['log', '--oneline', '$fromRef..$toRef']);
    if (!result.success) return [];

    return result.output
        .split('\n')
        .where((line) => line.trim().isNotEmpty)
        .map((line) => line.split(' ').first)
        .toList();
  }

  /// Get commit count
  Future<int> getCommitCount() async {
    final result = await _run(['rev-list', '--count', 'HEAD']);
    if (!result.success) return 0;
    return int.tryParse(result.output.trim()) ?? 0;
  }

  /// Check if there are unpushed commits
  Future<bool> hasUnpushedCommits() async {
    final result = await _run(['log', '@{u}..HEAD', '--oneline']);
    if (!result.success) return false;
    return result.output.trim().isNotEmpty;
  }

  /// Check if remote tracking is set up
  Future<bool> hasRemoteTracking() async {
    final result = await _run(['rev-parse', '--abbrev-ref', '@{u}']);
    return result.success;
  }

  /// Run a git command
  Future<GitResult> _run(
    List<String> args, {
    Map<String, String>? environment,
  }) async {
    try {
      final result = await Process.run(
        'git',
        args,
        workingDirectory: repoPath,
        environment: environment,
        stdoutEncoding: utf8,
        stderrEncoding: utf8,
      );

      return GitResult(
        success: result.exitCode == 0,
        output: result.stdout as String,
        error: result.exitCode != 0 ? result.stderr as String : null,
        exitCode: result.exitCode,
      );
    } catch (e) {
      return GitResult(
        success: false,
        output: '',
        error: e.toString(),
        exitCode: -1,
      );
    }
  }

  /// Format DateTime for git date environment variables
  String _formatGitDate(DateTime dt) {
    // Git accepts ISO 8601 format
    return dt.toIso8601String();
  }
}

/// Service for executing a commit plan
class ExecutionService {
  final GitAdapter git;
  final void Function(int current, int total, String message)? onProgress;

  ExecutionService({
    required this.git,
    this.onProgress,
  });

  /// Execute a plan, creating commits with proper dates
  Future<ExecutionResult> executePlan({
    required PlanSummary plan,
    required ContentGenerator contentGenerator,
    String? authorName,
    String? authorEmail,
    bool pushAfter = false,
  }) async {
    final filesCreated = <String>[];
    var successCount = 0;
    var failCount = 0;

    final allCommits = plan.allCommits;
    final total = allCommits.length;

    for (var i = 0; i < allCommits.length; i++) {
      final commit = allCommits[i];
      onProgress?.call(i + 1, total, 'Creating commit ${i + 1}/$total');

      try {
        // Generate content for this commit
        final filePath = await contentGenerator.generateContent(
          timestamp: commit.timestamp,
          repoPath: git.repoPath,
        );
        filesCreated.add(filePath);

        // Stage the file
        await git.add([filePath]);

        // Create commit with proper date
        final result = await git.createCommit(
          message: commit.message,
          timestamp: commit.timestamp,
          authorName: authorName,
          authorEmail: authorEmail,
        );

        if (result.success) {
          successCount++;
        } else {
          failCount++;
        }
      } catch (e) {
        failCount++;
      }
    }

    // Optional push
    bool pushed = false;
    String? pushError;
    if (pushAfter && successCount > 0) {
      onProgress?.call(total, total, 'Pushing to remote...');
      final pushResult = await git.push();
      pushed = pushResult.success;
      if (!pushResult.success) {
        pushError = pushResult.error;
      }
    }

    return ExecutionResult(
      totalCommits: total,
      successCount: successCount,
      failCount: failCount,
      filesCreated: filesCreated,
      pushed: pushed,
      pushError: pushError,
    );
  }
}

/// Result of plan execution
class ExecutionResult {
  final int totalCommits;
  final int successCount;
  final int failCount;
  final List<String> filesCreated;
  final bool pushed;
  final String? pushError;

  const ExecutionResult({
    required this.totalCommits,
    required this.successCount,
    required this.failCount,
    required this.filesCreated,
    required this.pushed,
    this.pushError,
  });

  bool get isSuccess => failCount == 0;
}

/// Abstract interface for content generation
abstract class ContentGenerator {
  Future<String> generateContent({
    required DateTime timestamp,
    required String repoPath,
  });
}
