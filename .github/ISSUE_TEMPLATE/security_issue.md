name: Security finding
description: Use this template to file and triage security findings produced by automated scans.
title: 'Security: [short description]'
labels: security, triage
body:
  - type: textarea
    attributes:
      label: Summary
      description: Brief summary of the finding.
      placeholder: "What was found?"
  - type: textarea
    attributes:
      label: Steps to reproduce
      description: Repro steps or links to CI artifacts.
  - type: checkbox
    attributes:
      label: Suggested severity
      options:
        - Low
        - Medium
        - High
        - Critical