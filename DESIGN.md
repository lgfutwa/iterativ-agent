---
version: alpha
name: Iterativ Studio
description: Calm workspace UI for agentic building.
colors:
  primary: "#111827"
  on-primary: "#FFFFFF"
  secondary: "#5F6B7A"
  tertiary: "#1A73E8"
  tertiary-soft: "#E8F0FE"
  success: "#188038"
  warning: "#F9AB00"
  danger: "#D93025"
  surface: "#FFFFFF"
  surface-subtle: "#F8FAFC"
  surface-raised: "#FFFFFF"
  border: "#DADCE0"
  border-subtle: "#E8EAED"
  text: "#111827"
  text-muted: "#5F6B7A"
  text-soft: "#8993A3"
  focus: "#8AB4F8"
  gemini-blue: "#8AB4F8"
  gemini-green: "#C6E7D4"
  gemini-yellow: "#FDD663"
  gemini-red: "#F6AEA9"
typography:
  display:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
    fontSize: 3.5rem
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "0"
  title:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
    fontSize: 1rem
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "0"
  body:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0"
  label:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
    fontSize: 0.875rem
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: "0"
  meta:
    fontFamily: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
    fontSize: 0.75rem
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "0"
rounded:
  sm: 8px
  md: 14px
  lg: 28px
  pill: 999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  xxl: 64px
components:
  shell:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
  sidebar:
    backgroundColor: "{colors.surface-subtle}"
    textColor: "{colors.text-muted}"
    width: 256px
  nav-item:
    backgroundColor: transparent
    textColor: "{colors.text-muted}"
    rounded: "{rounded.sm}"
    padding: 10px
  nav-item-active:
    backgroundColor: "{colors.border-subtle}"
    textColor: "{colors.text}"
    rounded: "{rounded.sm}"
  composer:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: 20px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.pill}"
    padding: 12px
  chip:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.pill}"
    padding: 10px
---

## Overview

Iterativ Studio is a quiet workspace for directing an agent. It should feel closer
to a focused creation tool than an admin dashboard: spacious canvas, clear input,
plain language, and subdued chrome that recedes until it is needed.

## Colors

The base palette is neutral and light. Ink is reserved for core actions and
headlines, Google-like blue carries interactive affordances, and the four Gemini
accent colors appear only as a thin composer edge or small icon highlight.

## Typography

Use the system sans stack everywhere. Keep letter spacing at zero and avoid
decorative uppercase. Display text should be large but not heavy; labels should
be compact, scannable, and calm.

## Layout

The first screen centers on a single composer. Navigation stays narrow and low
contrast. Status information belongs in pills and badges, never in large panels
unless it is the primary task.

## Elevation & Depth

Depth is functional. Use soft shadows on floating pills and the composer, but do
not stack cards inside cards. Borders should define structure before shadows do.

## Shapes

Repeated surfaces use 8px corners. The composer and compact command controls use
rounded pills because they behave like controls, not containers.

## Components

Primary actions use dark ink. Secondary actions use white surfaces with subtle
borders. Starter prompts are compact chips with an icon and label. The prompt
composer is the hero component and should remain the highest-contrast object on
the screen.

## Do's and Don'ts

Do keep the interface airy and task-focused. Do make controls obvious through
shape, icon, and proximity. Do preserve accessible contrast. Do not use heavy
marketing sections, nested cards, decorative background blobs, or one-note color
themes.
