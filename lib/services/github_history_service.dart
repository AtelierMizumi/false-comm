import 'dart:convert';
import 'package:http/http.dart' as http;
import '../domain/models.dart';

/// Service for fetching GitHub contribution history.
/// Supports both GraphQL API (with PAT) and HTML scraping (fallback).
class GitHubHistoryService {
  final http.Client _client;

  GitHubHistoryService({http.Client? client}) : _client = client ?? http.Client();

  /// Fetch contribution profile using the best available method
  Future<ContributionProfile?> fetchProfile(
    String username, {
    String? pat,
  }) async {
    // Try GraphQL first if PAT is available
    if (pat != null && pat.isNotEmpty) {
      try {
        final profile = await fetchViaGraphQL(username, pat);
        if (profile != null) return profile;
      } catch (_) {
        // Fall through to scrape
      }
    }

    // Fallback to HTML scraping
    return fetchViaScrape(username);
  }

  /// Fetch contributions using GitHub GraphQL API
  /// Requires a PAT with read:user scope
  Future<ContributionProfile?> fetchViaGraphQL(
    String username,
    String pat,
  ) async {
    const endpoint = 'https://api.github.com/graphql';

    // Query for contribution data from the last year
    final query = '''
    query {
      user(login: "$username") {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    ''';

    try {
      final response = await _client.post(
        Uri.parse(endpoint),
        headers: {
          'Authorization': 'Bearer $pat',
          'Content-Type': 'application/json',
        },
        body: json.encode({'query': query}),
      );

      if (response.statusCode != 200) {
        return null;
      }

      final data = json.decode(response.body) as Map<String, dynamic>;
      final user = data['data']?['user'] as Map<String, dynamic>?;
      if (user == null) return null;

      final calendar = user['contributionsCollection']?['contributionCalendar']
          as Map<String, dynamic>?;
      if (calendar == null) return null;

      final weeks = calendar['weeks'] as List<dynamic>?;
      if (weeks == null) return null;

      final contributions = <ContributionDay>[];

      for (final week in weeks) {
        final days = (week as Map<String, dynamic>)['contributionDays']
            as List<dynamic>?;
        if (days == null) continue;

        for (final day in days) {
          final dayData = day as Map<String, dynamic>;
          final dateStr = dayData['date'] as String?;
          final count = dayData['contributionCount'] as int?;

          if (dateStr != null && count != null) {
            contributions.add(ContributionDay(
              date: DateTime.parse(dateStr),
              count: count,
            ));
          }
        }
      }

      return ContributionProfile(
        username: username,
        contributions: contributions,
        fetchedAt: DateTime.now(),
      );
    } catch (e) {
      return null;
    }
  }

  /// Fetch contributions by scraping GitHub profile page
  /// This is a fallback when no PAT is available
  Future<ContributionProfile?> fetchViaScrape(String username) async {
    final url = 'https://github.com/users/$username/contributions';

    try {
      final response = await _client.get(
        Uri.parse(url),
        headers: {
          'Accept': 'text/html',
          'User-Agent': 'Mozilla/5.0 (compatible; FakeCommPlanner/1.0)',
        },
      );

      if (response.statusCode != 200) {
        return null;
      }

      final contributions = _parseContributionsSvg(response.body);
      if (contributions.isEmpty) return null;

      return ContributionProfile(
        username: username,
        contributions: contributions,
        fetchedAt: DateTime.now(),
      );
    } catch (e) {
      return null;
    }
  }

  /// Parse contribution data from GitHub's SVG calendar
  List<ContributionDay> _parseContributionsSvg(String html) {
    final contributions = <ContributionDay>[];

    // GitHub's contribution calendar uses <td> elements with data-date and data-level
    // Format: <td ... data-date="2024-01-15" data-level="2" ...>
    // or in newer format: <td ... data-date="2024-01-15" data-count="5" ...>

    // Try data-count pattern first (newer format)
    final countPattern = RegExp(
      r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-count="(\d+)"',
      multiLine: true,
    );

    for (final match in countPattern.allMatches(html)) {
      try {
        final dateStr = match.group(1);
        final countStr = match.group(2);
        if (dateStr != null && countStr != null) {
          contributions.add(ContributionDay(
            date: DateTime.parse(dateStr),
            count: int.parse(countStr),
          ));
        }
      } catch (_) {
        // Skip malformed entries
      }
    }

    if (contributions.isNotEmpty) return contributions;

    // Fallback to data-level pattern (older format)
    // data-level maps: 0=0, 1=1-3, 2=4-6, 3=7-9, 4=10+
    final levelPattern = RegExp(
      r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"',
      multiLine: true,
    );

    for (final match in levelPattern.allMatches(html)) {
      try {
        final dateStr = match.group(1);
        final levelStr = match.group(2);
        if (dateStr != null && levelStr != null) {
          final level = int.parse(levelStr);
          // Map level to approximate count
          final count = _levelToApproximateCount(level);
          contributions.add(ContributionDay(
            date: DateTime.parse(dateStr),
            count: count,
          ));
        }
      } catch (_) {
        // Skip malformed entries
      }
    }

    // Also try reverse order (data-level before data-date)
    if (contributions.isEmpty) {
      final reverseLevelPattern = RegExp(
        r'data-level="(\d)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"',
        multiLine: true,
      );

      for (final match in reverseLevelPattern.allMatches(html)) {
        try {
          final levelStr = match.group(1);
          final dateStr = match.group(2);
          if (dateStr != null && levelStr != null) {
            final level = int.parse(levelStr);
            final count = _levelToApproximateCount(level);
            contributions.add(ContributionDay(
              date: DateTime.parse(dateStr),
              count: count,
            ));
          }
        } catch (_) {
          // Skip malformed entries
        }
      }
    }

    return contributions;
  }

  /// Map GitHub's contribution level (0-4) to approximate commit count
  int _levelToApproximateCount(int level) {
    switch (level) {
      case 0:
        return 0;
      case 1:
        return 2; // 1-3 contributions
      case 2:
        return 5; // 4-6 contributions
      case 3:
        return 8; // 7-9 contributions
      case 4:
        return 12; // 10+ contributions
      default:
        return 0;
    }
  }

  /// Verify that a PAT is valid for reading contributions
  Future<bool> verifyPat(String pat) async {
    const endpoint = 'https://api.github.com/graphql';

    const query = '''
    query {
      viewer {
        login
      }
    }
    ''';

    try {
      final response = await _client.post(
        Uri.parse(endpoint),
        headers: {
          'Authorization': 'Bearer $pat',
          'Content-Type': 'application/json',
        },
        body: json.encode({'query': query}),
      );

      if (response.statusCode != 200) return false;

      final data = json.decode(response.body) as Map<String, dynamic>;
      final viewer = data['data']?['viewer'] as Map<String, dynamic>?;
      return viewer != null && viewer['login'] != null;
    } catch (e) {
      return false;
    }
  }

  /// Get the authenticated user's login (to verify PAT matches expected user)
  Future<String?> getAuthenticatedLogin(String pat) async {
    const endpoint = 'https://api.github.com/graphql';

    const query = '''
    query {
      viewer {
        login
      }
    }
    ''';

    try {
      final response = await _client.post(
        Uri.parse(endpoint),
        headers: {
          'Authorization': 'Bearer $pat',
          'Content-Type': 'application/json',
        },
        body: json.encode({'query': query}),
      );

      if (response.statusCode != 200) return null;

      final data = json.decode(response.body) as Map<String, dynamic>;
      return data['data']?['viewer']?['login'] as String?;
    } catch (e) {
      return null;
    }
  }

  void dispose() {
    _client.close();
  }
}
