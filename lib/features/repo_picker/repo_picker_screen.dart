import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/models.dart';
import '../../providers/providers.dart';
import '../../services/git_adapter.dart';

class RepoPickerScreen extends ConsumerStatefulWidget {
  final VoidCallback onNext;

  const RepoPickerScreen({super.key, required this.onNext});

  @override
  ConsumerState<RepoPickerScreen> createState() => _RepoPickerScreenState();
}

class _RepoPickerScreenState extends ConsumerState<RepoPickerScreen> {
  final _pathController = TextEditingController();
  bool _isValidating = false;
  RepoConfig? _validatedConfig;
  String? _error;

  @override
  void initState() {
    super.initState();
    final currentConfig = ref.read(repoConfigProvider);
    if (currentConfig.path.isNotEmpty) {
      _pathController.text = currentConfig.path;
      _validatedConfig = currentConfig;
    }
  }

  @override
  void dispose() {
    _pathController.dispose();
    super.dispose();
  }

  Future<void> _validatePath() async {
    final path = _pathController.text.trim();
    if (path.isEmpty) {
      setState(() {
        _error = 'Please enter a repository path';
        _validatedConfig = null;
      });
      return;
    }

    setState(() {
      _isValidating = true;
      _error = null;
    });

    try {
      final git = GitAdapter(path);
      final config = await git.validateRepo();

      setState(() {
        _isValidating = false;
        _validatedConfig = config;
        if (!config.isValid) {
          _error = 'Not a valid Git repository';
        }
      });
    } catch (e) {
      setState(() {
        _isValidating = false;
        _error = 'Error validating repository: $e';
        _validatedConfig = null;
      });
    }
  }

  Future<void> _browsePath() async {
    // Simple path browsing - in a real app, use file_picker package
    // For now, just show a dialog to enter path manually
    final result = await showDialog<String>(
      context: context,
      builder: (context) => _PathInputDialog(
        initialPath: _pathController.text,
      ),
    );

    if (result != null && result.isNotEmpty) {
      _pathController.text = result;
      await _validatePath();
    }
  }

  void _proceed() {
    if (_validatedConfig != null && _validatedConfig!.isValid) {
      ref.read(appStateProvider.notifier).setRepoConfig(_validatedConfig!);
      widget.onNext();
    }
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
            'Select Repository',
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Choose the local Git repository where fake commits will be created.',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 32),

          // Path input
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _pathController,
                  decoration: InputDecoration(
                    labelText: 'Repository Path',
                    hintText: Platform.isWindows
                        ? 'C:\\Users\\...\\my-repo'
                        : '/home/.../my-repo',
                    border: const OutlineInputBorder(),
                    prefixIcon: const Icon(Icons.folder),
                    errorText: _error,
                  ),
                  onSubmitted: (_) => _validatePath(),
                ),
              ),
              const SizedBox(width: 12),
              ElevatedButton.icon(
                onPressed: _browsePath,
                icon: const Icon(Icons.folder_open),
                label: const Text('Browse'),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: _isValidating ? null : _validatePath,
                child: _isValidating
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Validate'),
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Validation result
          if (_validatedConfig != null) _buildValidationResult(theme),

          const Spacer(),

          // Navigation
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              FilledButton.icon(
                onPressed: _validatedConfig?.isValid == true ? _proceed : null,
                icon: const Icon(Icons.arrow_forward),
                label: const Text('Next: Identity'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildValidationResult(ThemeData theme) {
    final config = _validatedConfig!;

    if (!config.isValid) {
      return Card(
        color: theme.colorScheme.errorContainer,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(Icons.error, color: theme.colorScheme.error),
              const SizedBox(width: 12),
              Text(
                'Not a valid Git repository',
                style: TextStyle(color: theme.colorScheme.onErrorContainer),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      color: theme.colorScheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.check_circle, color: theme.colorScheme.primary),
                const SizedBox(width: 12),
                Text(
                  'Valid Git Repository',
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: theme.colorScheme.onPrimaryContainer,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _buildInfoRow('Branch', config.branch, Icons.account_tree),
            if (config.gitVersion != null)
              _buildInfoRow('Git Version', config.gitVersion!, Icons.terminal),
            if (config.remoteUrl != null)
              _buildInfoRow('Remote', config.remoteUrl!, Icons.cloud),
            if (config.isDirty)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Row(
                  children: [
                    Icon(Icons.warning, color: theme.colorScheme.tertiary, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      'Repository has uncommitted changes',
                      style: TextStyle(color: theme.colorScheme.tertiary),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, IconData icon) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 18, color: Colors.grey),
          const SizedBox(width: 8),
          SizedBox(
            width: 100,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(
            child: Text(
              value,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

class _PathInputDialog extends StatefulWidget {
  final String initialPath;

  const _PathInputDialog({required this.initialPath});

  @override
  State<_PathInputDialog> createState() => _PathInputDialogState();
}

class _PathInputDialogState extends State<_PathInputDialog> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialPath);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Enter Repository Path'),
      content: TextField(
        controller: _controller,
        autofocus: true,
        decoration: const InputDecoration(
          labelText: 'Full path to repository',
          border: OutlineInputBorder(),
        ),
        onSubmitted: (_) => Navigator.of(context).pop(_controller.text.trim()),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context).pop(_controller.text.trim()),
          child: const Text('OK'),
        ),
      ],
    );
  }
}
