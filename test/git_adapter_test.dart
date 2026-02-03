import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:fake_comm_gui/services/git_adapter.dart';

void main() {
  group('GitAdapter Static Tests', () {
    test('getGitVersion returns version string', () async {
      final version = await GitAdapter.getGitVersion();
      
      // Git should be installed
      expect(version, isNotNull);
      expect(version!.contains('git version'), true);
    });
  });

  group('GitAdapter Repository Tests', () {
    late Directory tempDir;
    late GitAdapter git;

    setUp(() async {
      // Create temp directory for test repo
      tempDir = await Directory.systemTemp.createTemp('fake_comm_test_');
      git = GitAdapter(tempDir.path);

      // Initialize git repo
      await Process.run('git', ['init'], workingDirectory: tempDir.path);
      await Process.run('git', ['config', 'user.email', 'test@test.com'], 
          workingDirectory: tempDir.path);
      await Process.run('git', ['config', 'user.name', 'Test User'], 
          workingDirectory: tempDir.path);
      
      // Create initial commit
      final testFile = File('${tempDir.path}/README.md');
      await testFile.writeAsString('# Test Repo\n');
      await Process.run('git', ['add', '.'], workingDirectory: tempDir.path);
      await Process.run('git', ['commit', '-m', 'Initial commit'], 
          workingDirectory: tempDir.path);
    });

    tearDown(() async {
      // Cleanup
      if (await tempDir.exists()) {
        await tempDir.delete(recursive: true);
      }
    });

    test('validateRepo detects valid git repo', () async {
      final config = await git.validateRepo();

      expect(config.isValid, true);
      expect(config.path, tempDir.path);
      expect(config.branch.isNotEmpty, true);
      expect(config.gitVersion, isNotNull);
    });

    test('validateRepo detects invalid directory', () async {
      final invalidGit = GitAdapter('${tempDir.path}/nonexistent');
      final config = await invalidGit.validateRepo();

      expect(config.isValid, false);
    });

    test('validateRepo detects non-git directory', () async {
      final nonGitDir = await Directory('${tempDir.path}/not_a_repo').create();
      final nonGit = GitAdapter(nonGitDir.path);
      final config = await nonGit.validateRepo();

      expect(config.isValid, false);
    });

    test('getHeadCommit returns SHA', () async {
      final sha = await git.getHeadCommit();

      expect(sha, isNotNull);
      expect(sha!.length >= 7, true); // At least short SHA
    });

    test('getConfiguredEmail returns email', () async {
      final email = await git.getConfiguredEmail();

      expect(email, 'test@test.com');
    });

    test('getConfiguredName returns name', () async {
      final name = await git.getConfiguredName();

      expect(name, 'Test User');
    });

    test('add and commit creates new commit', () async {
      // Create a new file
      final newFile = File('${tempDir.path}/new_file.txt');
      await newFile.writeAsString('New content\n');

      // Get initial HEAD
      final initialHead = await git.getHeadCommit();

      // Add and commit
      await git.add(['new_file.txt']);
      final result = await git.createCommit(
        message: 'Add new file',
        timestamp: DateTime(2024, 1, 15, 10, 30),
      );

      expect(result.success, true);

      // HEAD should be different now
      final newHead = await git.getHeadCommit();
      expect(newHead != initialHead, true);
    });

    test('createCommit with custom date sets author/committer date', () async {
      // Create a file
      final file = File('${tempDir.path}/dated_file.txt');
      await file.writeAsString('Dated content\n');

      await git.add(['dated_file.txt']);
      final result = await git.createCommit(
        message: 'Dated commit',
        timestamp: DateTime(2023, 6, 15, 14, 30),
        authorName: 'Custom Author',
        authorEmail: 'custom@author.com',
      );

      expect(result.success, true);

      // Verify the commit date using git log
      final logResult = await Process.run(
        'git',
        ['log', '-1', '--format=%ai'],
        workingDirectory: tempDir.path,
      );

      final dateOutput = (logResult.stdout as String).trim();
      expect(dateOutput.contains('2023-06-15'), true);
    });

    test('getCommitCount returns correct count', () async {
      final count = await git.getCommitCount();
      
      // We created 1 initial commit in setUp
      expect(count >= 1, true);
    });

    test('resetHard resets to specified commit', () async {
      // Get initial HEAD
      final initialHead = await git.getHeadCommit();

      // Create new commit
      final file = File('${tempDir.path}/to_reset.txt');
      await file.writeAsString('Content\n');
      await git.add(['to_reset.txt']);
      await git.createCommit(
        message: 'Commit to reset',
        timestamp: DateTime.now(),
      );

      // Verify HEAD changed
      final afterCommitHead = await git.getHeadCommit();
      expect(afterCommitHead != initialHead, true);

      // Reset
      final resetResult = await git.resetHard(initialHead!);
      expect(resetResult.success, true);

      // Verify HEAD is back to initial
      final resetHead = await git.getHeadCommit();
      expect(resetHead, initialHead);

      // File should be gone
      expect(await file.exists(), false);
    });

    test('isDirty detects uncommitted changes', () async {
      // Initially should be clean
      var config = await git.validateRepo();
      expect(config.isDirty, false);

      // Create uncommitted file
      final file = File('${tempDir.path}/dirty_file.txt');
      await file.writeAsString('Dirty content\n');
      await git.add(['dirty_file.txt']);

      // Should now be dirty
      config = await git.validateRepo();
      expect(config.isDirty, true);
    });
  });

  group('GitResult Tests', () {
    test('success result has correct properties', () {
      const result = GitResult(
        success: true,
        output: 'Some output',
        exitCode: 0,
      );

      expect(result.success, true);
      expect(result.output, 'Some output');
      expect(result.error, isNull);
      expect(result.exitCode, 0);
    });

    test('failure result has error', () {
      const result = GitResult(
        success: false,
        output: '',
        error: 'Something went wrong',
        exitCode: 1,
      );

      expect(result.success, false);
      expect(result.error, 'Something went wrong');
      expect(result.exitCode, 1);
    });
  });
}
