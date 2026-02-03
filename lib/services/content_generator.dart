import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:intl/intl.dart';
import 'git_adapter.dart';

/// Service for generating minimal, realistic file content for commits.
/// Creates notes files and progress.json to look like actual development work.
class ContentGeneratorService implements ContentGenerator {
  final Random _random;
  final List<String> _commitMessages;

  ContentGeneratorService({
    Random? random,
    List<String>? customMessages,
  })  : _random = random ?? Random(),
        _commitMessages = customMessages ?? defaultCommitMessages;

  /// Default pool of realistic commit messages
  static const List<String> defaultCommitMessages = [
    'chore: log daily notes',
    'docs: capture findings',
    'notes: update ideas list',
    'refactor: adjust checklist wording',
    'chore: update progress tracking',
    'docs: add meeting notes',
    'notes: document research findings',
    'chore: organize task list',
    'docs: update project notes',
    'notes: capture thoughts',
    'chore: clean up notes structure',
    'docs: add implementation ideas',
    'notes: record decision rationale',
    'chore: sync progress file',
    'docs: document approach',
    'notes: add todo items',
    'chore: update tracking info',
    'docs: refine documentation',
    'notes: clarify requirements',
    'chore: maintain notes consistency',
  ];

  /// Pool of note bullet points
  static const List<String> _noteBullets = [
    'Reviewed project requirements and identified key areas',
    'Explored different implementation approaches',
    'Researched best practices for current task',
    'Documented findings from code review session',
    'Outlined next steps for feature development',
    'Noted potential edge cases to handle',
    'Captured feedback from team discussion',
    'Updated task priorities based on new info',
    'Recorded architecture decision rationale',
    'Identified areas needing refactoring',
    'Listed dependencies to evaluate',
    'Summarized testing strategy thoughts',
    'Noted performance optimization ideas',
    'Documented API design considerations',
    'Captured user experience improvements',
    'Outlined documentation needs',
    'Recorded debugging session findings',
    'Listed configuration options to consider',
    'Noted security considerations',
    'Captured deployment process notes',
    'Reviewed error handling approaches',
    'Documented state management options',
    'Outlined integration testing needs',
    'Recorded accessibility requirements',
    'Listed localization considerations',
  ];

  /// Pool of progress entry descriptions
  static const List<String> _progressEntries = [
    'feature exploration',
    'code review',
    'documentation update',
    'refactoring session',
    'bug investigation',
    'architecture planning',
    'testing improvements',
    'performance analysis',
    'dependency evaluation',
    'security review',
    'UI/UX refinement',
    'API design work',
    'data modeling',
    'integration work',
    'deployment prep',
  ];

  /// Get the list of available commit messages
  List<String> get commitMessages => List.unmodifiable(_commitMessages);

  /// Generate a random commit message
  String getRandomMessage() {
    return _commitMessages[_random.nextInt(_commitMessages.length)];
  }

  @override
  Future<String> generateContent({
    required DateTime timestamp,
    required String repoPath,
  }) async {
    // Decide between notes file or progress update
    final useNotes = _random.nextDouble() > 0.3; // 70% notes, 30% progress

    if (useNotes) {
      return _generateNotesFile(timestamp, repoPath);
    } else {
      return _generateProgressUpdate(timestamp, repoPath);
    }
  }

  /// Generate a notes markdown file for a specific date
  Future<String> _generateNotesFile(DateTime timestamp, String repoPath) async {
    final dateStr = DateFormat('yyyy-MM-dd').format(timestamp);
    final dirPath = '$repoPath/notes';
    final filePath = '$dirPath/$dateStr.md';

    // Ensure notes directory exists
    final dir = Directory(dirPath);
    if (!await dir.exists()) {
      await dir.create(recursive: true);
    }

    // Generate 2-4 random bullet points
    final bulletCount = 2 + _random.nextInt(3);
    final bullets = <String>[];
    final usedIndices = <int>{};

    while (bullets.length < bulletCount) {
      final index = _random.nextInt(_noteBullets.length);
      if (!usedIndices.contains(index)) {
        usedIndices.add(index);
        bullets.add(_noteBullets[index]);
      }
    }

    // Build content
    final timeStr = DateFormat('HH:mm').format(timestamp);
    final content = StringBuffer();
    content.writeln('# Notes - $dateStr');
    content.writeln();
    content.writeln('## $timeStr Update');
    content.writeln();
    for (final bullet in bullets) {
      content.writeln('- $bullet');
    }
    content.writeln();

    // If file exists, append to it; otherwise create new
    final file = File(filePath);
    if (await file.exists()) {
      final existing = await file.readAsString();
      // Append new section
      final newContent = '$existing\n## $timeStr Update\n\n';
      final bulletSection = bullets.map((b) => '- $b').join('\n');
      await file.writeAsString('$newContent$bulletSection\n');
    } else {
      await file.writeAsString(content.toString());
    }

    return filePath;
  }

  /// Generate or update progress.json
  Future<String> _generateProgressUpdate(
      DateTime timestamp, String repoPath) async {
    final filePath = '$repoPath/progress.json';
    final file = File(filePath);

    Map<String, dynamic> progress;
    if (await file.exists()) {
      try {
        final content = await file.readAsString();
        progress = json.decode(content) as Map<String, dynamic>;
      } catch (_) {
        progress = _createInitialProgress();
      }
    } else {
      progress = _createInitialProgress();
    }

    // Update progress
    _updateProgress(progress, timestamp);

    // Write back
    const encoder = JsonEncoder.withIndent('  ');
    await file.writeAsString(encoder.convert(progress));

    return filePath;
  }

  Map<String, dynamic> _createInitialProgress() {
    return {
      'version': '1.0.0',
      'created': DateTime.now().toIso8601String(),
      'lastUpdated': DateTime.now().toIso8601String(),
      'entries': <Map<String, dynamic>>[],
      'stats': {
        'totalSessions': 0,
        'focusAreas': <String>[],
      },
    };
  }

  void _updateProgress(Map<String, dynamic> progress, DateTime timestamp) {
    // Update last updated
    progress['lastUpdated'] = timestamp.toIso8601String();

    // Add new entry
    final entries = progress['entries'] as List<dynamic>;
    final entry = _progressEntries[_random.nextInt(_progressEntries.length)];

    entries.add({
      'timestamp': timestamp.toIso8601String(),
      'activity': entry,
      'duration': '${15 + _random.nextInt(90)}min',
    });

    // Keep only last 50 entries to avoid file bloat
    if (entries.length > 50) {
      progress['entries'] = entries.sublist(entries.length - 50);
    }

    // Update stats
    final stats = progress['stats'] as Map<String, dynamic>;
    stats['totalSessions'] = (stats['totalSessions'] as int? ?? 0) + 1;

    final focusAreas = List<String>.from(stats['focusAreas'] as List? ?? []);
    if (!focusAreas.contains(entry)) {
      focusAreas.add(entry);
      if (focusAreas.length > 10) {
        focusAreas.removeAt(0);
      }
      stats['focusAreas'] = focusAreas;
    }
  }

  /// Clean up generated files (for undo)
  Future<void> cleanupFiles(String repoPath, List<String> files) async {
    for (final filePath in files) {
      final file = File(filePath);
      if (await file.exists()) {
        await file.delete();
      }
    }

    // Try to clean up empty notes directory
    final notesDir = Directory('$repoPath/notes');
    if (await notesDir.exists()) {
      final remaining = await notesDir.list().length;
      if (remaining == 0) {
        await notesDir.delete();
      }
    }

    // Remove progress.json if empty
    final progressFile = File('$repoPath/progress.json');
    if (await progressFile.exists()) {
      try {
        final content = await progressFile.readAsString();
        final progress = json.decode(content) as Map<String, dynamic>;
        final entries = progress['entries'] as List?;
        if (entries == null || entries.isEmpty) {
          await progressFile.delete();
        }
      } catch (_) {
        // Leave file if can't parse
      }
    }
  }
}
