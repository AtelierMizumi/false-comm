import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/models.dart';
import '../../providers/providers.dart';

class IdentityScreen extends ConsumerStatefulWidget {
  final VoidCallback onNext;
  final VoidCallback onBack;

  const IdentityScreen({
    super.key,
    required this.onNext,
    required this.onBack,
  });

  @override
  ConsumerState<IdentityScreen> createState() => _IdentityScreenState();
}

class _IdentityScreenState extends ConsumerState<IdentityScreen> {
  final _usernameController = TextEditingController();
  final _emailController = TextEditingController();
  final _patController = TextEditingController();
  String _selectedTimezone = 'Asia/Ho_Chi_Minh';
  bool _fetchContributions = false;
  bool _isFetching = false;
  String? _fetchError;
  ContributionProfile? _fetchedProfile;

  static const List<String> _commonTimezones = [
    'Asia/Ho_Chi_Minh',
    'Asia/Tokyo',
    'Asia/Seoul',
    'Asia/Shanghai',
    'Asia/Singapore',
    'America/New_York',
    'America/Los_Angeles',
    'America/Chicago',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Australia/Sydney',
    'Pacific/Auckland',
  ];

  @override
  void initState() {
    super.initState();
    final currentConfig = ref.read(identityConfigProvider);
    if (currentConfig.username.isNotEmpty) {
      _usernameController.text = currentConfig.username;
      _emailController.text = currentConfig.email;
      _selectedTimezone = currentConfig.timezone;
      if (currentConfig.githubPat != null) {
        _patController.text = currentConfig.githubPat!;
        _fetchContributions = true;
      }
    }

    final profile = ref.read(contributionProfileProvider);
    if (profile != null) {
      _fetchedProfile = profile;
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _emailController.dispose();
    _patController.dispose();
    super.dispose();
  }

  Future<void> _fetchContributionProfile() async {
    final username = _usernameController.text.trim();
    if (username.isEmpty) {
      setState(() => _fetchError = 'Please enter a GitHub username first');
      return;
    }

    setState(() {
      _isFetching = true;
      _fetchError = null;
    });

    try {
      final service = ref.read(githubHistoryServiceProvider);
      final pat = _patController.text.trim();
      final profile = await service.fetchProfile(
        username,
        pat: pat.isNotEmpty ? pat : null,
      );

      if (mounted) {
        setState(() {
          _isFetching = false;
          _fetchedProfile = profile;
          if (profile == null) {
            _fetchError = 'Could not fetch contribution data. Check username or try adding a PAT.';
          }
        });

        if (profile != null) {
          ref.read(appStateProvider.notifier).setContributionProfile(profile);
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isFetching = false;
          _fetchError = 'Error: $e';
        });
      }
    }
  }

  bool _isValid() {
    return _usernameController.text.trim().isNotEmpty &&
        _emailController.text.trim().isNotEmpty &&
        _emailController.text.contains('@');
  }

  void _proceed() {
    if (!_isValid()) return;

    final config = IdentityConfig(
      username: _usernameController.text.trim(),
      email: _emailController.text.trim(),
      timezone: _selectedTimezone,
      githubPat: _fetchContributions ? _patController.text.trim() : null,
    );

    ref.read(appStateProvider.notifier).setIdentityConfig(config);
    widget.onNext();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Identity Configuration',
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Configure your Git identity and optionally import your GitHub contribution pattern.',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 32),

          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Username
                  TextField(
                    controller: _usernameController,
                    decoration: const InputDecoration(
                      labelText: 'GitHub Username',
                      hintText: 'your-username',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.person),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Email
                  TextField(
                    controller: _emailController,
                    decoration: const InputDecoration(
                      labelText: 'Git Email',
                      hintText: 'you@example.com',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.email),
                    ),
                    keyboardType: TextInputType.emailAddress,
                  ),
                  const SizedBox(height: 16),

                  // Timezone
                  DropdownButtonFormField<String>(
                    initialValue: _selectedTimezone,
                    decoration: const InputDecoration(
                      labelText: 'Timezone',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.schedule),
                    ),
                    items: _commonTimezones.map((tz) {
                      return DropdownMenuItem(
                        value: tz,
                        child: Text(tz),
                      );
                    }).toList(),
                    onChanged: (value) {
                      if (value != null) {
                        setState(() => _selectedTimezone = value);
                      }
                    },
                  ),
                  const SizedBox(height: 24),

                  // Fetch contributions section
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: SwitchListTile(
                                  contentPadding: EdgeInsets.zero,
                                  title: const Text('Import GitHub Contribution Pattern'),
                                  subtitle: const Text(
                                    'Mirror your actual contribution style for more natural-looking commits',
                                  ),
                                  value: _fetchContributions,
                                  onChanged: (value) {
                                    setState(() => _fetchContributions = value);
                                  },
                                ),
                              ),
                            ],
                          ),

                          if (_fetchContributions) ...[
                            const SizedBox(height: 16),
                            TextField(
                              controller: _patController,
                              decoration: const InputDecoration(
                                labelText: 'GitHub Personal Access Token (optional)',
                                hintText: 'ghp_xxxx... (read:user scope)',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.key),
                                helperText: 'Leave empty to use HTML scraping (less accurate)',
                              ),
                              obscureText: true,
                            ),
                            const SizedBox(height: 16),
                            Row(
                              children: [
                                ElevatedButton.icon(
                                  onPressed: _isFetching ? null : _fetchContributionProfile,
                                  icon: _isFetching
                                      ? const SizedBox(
                                          width: 18,
                                          height: 18,
                                          child: CircularProgressIndicator(strokeWidth: 2),
                                        )
                                      : const Icon(Icons.download),
                                  label: Text(_isFetching ? 'Fetching...' : 'Fetch Profile'),
                                ),
                                if (_fetchedProfile != null) ...[
                                  const SizedBox(width: 12),
                                  Icon(Icons.check_circle, color: theme.colorScheme.primary),
                                  const SizedBox(width: 4),
                                  Text(
                                    '${_fetchedProfile!.contributions.length} days loaded',
                                    style: TextStyle(color: theme.colorScheme.primary),
                                  ),
                                ],
                              ],
                            ),
                            if (_fetchError != null)
                              Padding(
                                padding: const EdgeInsets.only(top: 8),
                                child: Text(
                                  _fetchError!,
                                  style: TextStyle(color: theme.colorScheme.error),
                                ),
                              ),
                            if (_fetchedProfile != null)
                              Padding(
                                padding: const EdgeInsets.only(top: 16),
                                child: _buildProfileSummary(theme),
                              ),
                          ],
                        ],
                      ),
                    ),
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
                onPressed: _isValid() ? _proceed : null,
                icon: const Icon(Icons.arrow_forward),
                label: const Text('Next: Behavior'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildProfileSummary(ThemeData theme) {
    final profile = _fetchedProfile!;
    final avgIntensity = profile.averageIntensity.toStringAsFixed(1);
    final weekdayWeights = profile.weekdayWeights;

    return Card(
      color: theme.colorScheme.surfaceContainerHighest,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Contribution Profile Summary',
              style: theme.textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            Text('Average: $avgIntensity commits/day'),
            const SizedBox(height: 4),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                for (final entry in weekdayWeights.entries)
                  Chip(
                    label: Text(
                      '${_weekdayName(entry.key)}: ${(entry.value * 100).toStringAsFixed(0)}%',
                    ),
                    visualDensity: VisualDensity.compact,
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _weekdayName(int day) {
    const names = ['', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return names[day];
  }
}
