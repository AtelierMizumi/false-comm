// Widget tests for FakeComm app

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fake_comm_gui/main.dart';

void main() {
  testWidgets('App starts and shows title', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(
      const ProviderScope(
        child: FakeCommApp(),
      ),
    );

    // Wait for the app to settle
    await tester.pumpAndSettle();

    // Verify app shell is shown with FakeComm title
    expect(find.text('FakeComm'), findsOneWidget);
    expect(find.text('Commit Planner'), findsOneWidget);
  });

  testWidgets('Navigation rail shows all steps', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: FakeCommApp(),
      ),
    );

    await tester.pumpAndSettle();

    // Verify all steps are shown in the navigation rail
    expect(find.text('Repository'), findsOneWidget);
    expect(find.text('Identity'), findsOneWidget);
    expect(find.text('Behavior'), findsOneWidget);
    expect(find.text('Preview'), findsOneWidget);
    expect(find.text('Execute'), findsOneWidget);
    expect(find.text('Run History'), findsOneWidget);
  });

  testWidgets('Repo picker screen shows initially', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: FakeCommApp(),
      ),
    );

    await tester.pumpAndSettle();

    // Verify repo picker screen content
    expect(find.text('Select Repository'), findsOneWidget);
    expect(find.text('Repository Path'), findsOneWidget);
    expect(find.text('Browse'), findsOneWidget);
    expect(find.text('Validate'), findsOneWidget);
  });

  testWidgets('Next button is disabled without valid repo', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: FakeCommApp(),
      ),
    );

    await tester.pumpAndSettle();

    // Find the Next button text
    final nextButtonText = find.text('Next: Identity');
    expect(nextButtonText, findsOneWidget);

    // Find the ButtonStyleButton ancestor (base class for FilledButton.icon)
    final buttonFinder = find.ancestor(
      of: nextButtonText,
      matching: find.byWidgetPredicate((widget) => widget is ButtonStyleButton),
    );
    expect(buttonFinder, findsOneWidget);

    // Button should be disabled (null onPressed)
    final button = tester.widget<ButtonStyleButton>(buttonFinder);
    expect(button.onPressed, isNull);
  });
}
