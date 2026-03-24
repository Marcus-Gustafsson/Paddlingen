# Web Development Tips

Last updated: 2026-03-24

## Purpose

This guide explains how to go from:

- seeing an element in the browser dev tools,

to:

- finding the right file in this project,
- understanding whether the value comes from HTML, CSS, JavaScript, or Flask,
- changing it safely.

This is written for a beginner and uses this project as the example.

## The Main Idea

When you inspect an element in the browser, you are looking at the final HTML
that the browser received.

That final result can come from several places:

1. a Jinja template in `templates/`
2. JavaScript in `static/js/`
3. CSS in `static/css/`
4. Flask route logic in `app/routes.py`
5. helper code in `app/util/`

So the browser shows the final output, but not always the original source file.

## Fast Rule Of Thumb

Use this rule first:

1. If the text is written directly in the page source and does not change after
   clicking buttons, it is often in `templates/`.
2. If the element appears only after clicking something, it is often created or
   updated in `static/js/`.
3. If the problem is spacing, font size, colors, hiding, stacking, or layout,
   it is usually in `static/css/`.
4. If the content depends on bookings, events, or database values, the source
   may be in `app/routes.py` or `app/util/`.

## Example: Change `?` To `Namn saknas`

If you inspect this:

```html
<span class="booking-summary-item-line">?</span>
```

that does **not** mean the `?` is written in an HTML template.

In this project, that specific text is generated in JavaScript.

The place to change it is:

- [booking.js](/home/marcgust/workspace/github.com/Marcus-Gustafsson/Paddling/static/js/booking.js)

The relevant code is inside the booking summary builder:

```js
const secondRiderName = buildFullName(
  passengerTwoFirstNameInput ? passengerTwoFirstNameInput.value.trim() : "",
  passengerTwoLastNameInput ? passengerTwoLastNameInput.value.trim() : "",
  "?"
);
```

and similarly for rider 3.

If you want the fallback to say `Namn saknas` instead, change the fallback
string from:

```js
"?"
```

to:

```js
"Namn saknas"
```

Why this is in JavaScript:

- the booking summary is built dynamically in the browser,
- so the text is inserted by `static/js/booking.js`,
- not pre-written in `templates/index.html`.

## Step-By-Step: How To Find The Source Of An Inspected Element

### Case 1: You know the class name

Example:

```html
<span class="booking-summary-item-line">?</span>
```

Search the project for the class name:

```bash
grep -RIn "booking-summary-item-line" templates static app
```

What this tells you:

- if it appears in a template, the HTML structure may come from there
- if it appears in JavaScript, the element may be created dynamically
- if it appears in CSS, that file controls the styling

For this example, you would find:

- structure and creation in `static/js/booking.js`
- styling in `static/css/booking.css`

### Case 2: You know the visible text

Example text:

```text
Lägg till en person
```

Search by text:

```bash
grep -RIn "Lägg till en person" templates static app
```

This is useful when the class name is generic but the text is unique.

### Case 3: You know the button or element only appears after clicking

If the element appears after interaction:

- modals opening,
- booking summary updating,
- form rows appearing,

then search `static/js/` first.

For example:

- public booking behavior lives mostly in `static/js/booking.js`
- admin panel behavior lives mostly in `static/js/admin_dashboard.js`
- overview modal behavior lives mostly in `static/js/modals.js`

### Case 4: The issue is only styling

If the element is structurally correct, but looks wrong:

- wrong spacing
- wrong font size
- wrong alignment
- hidden/shown incorrectly

search the CSS files:

```bash
grep -RIn "booking-summary-item-line" static/css
```

or:

```bash
grep -RIn "admin-inline-link" static/css
```

## How To Read The Browser Inspect View

When you inspect an element, look at these parts:

### 1. Tag name

Example:

```html
span
button
section
div
```

This tells you what kind of element it is.

### 2. Class names

Example:

```html
class="booking-summary-item-line"
```

This is often the easiest thing to search for in the repo.

### 3. Attributes

Example:

```html
data-admin-add-rider
aria-controls="adminAddSecondRider"
hidden
```

These are very useful clues.

In this project:

- `data-*` attributes usually point to JavaScript behavior
- `aria-*` often points to toggle behavior or accessibility logic
- `hidden` often means JavaScript or CSS is controlling visibility

## How To Decide Which File Type To Change

Use this checklist:

### Change the template in `templates/` when:

- the element exists from the first page load
- the text is static
- the overall HTML structure should change

Examples:

- card order
- heading text
- adding a new section to a modal

### Change JavaScript in `static/js/` when:

- the element is created after clicking
- the text changes dynamically
- rows appear/disappear
- the browser updates a summary without reloading

Examples:

- booking summary text
- add/remove rider buttons
- modal open/close state

### Change CSS in `static/css/` when:

- the content is correct but looks wrong
- mobile layout is wrong
- spacing or typography is wrong
- hidden elements still look visible

Examples:

- alignment
- colors
- widths
- padding
- `display: none`

### Change Python in `app/` when:

- the page shows wrong data from the database
- validation rules are wrong
- booking limits are wrong
- admin updates save the wrong values

Examples:

- max 5 canoes per pickup person
- optional rider validation
- admin save/update behavior

## Recommended Manual Workflow

When you find a UI issue in the browser:

1. Inspect the element.
2. Write down:
   - tag name
   - class name
   - any `data-*` attributes
   - the visible text
3. Search by class name first:

```bash
grep -RIn "CLASS_NAME_HERE" templates static app
```

4. If needed, search by text:

```bash
grep -RIn "VISIBLE TEXT HERE" templates static app
```

5. Decide:
   - HTML structure problem -> template
   - dynamic behavior problem -> JavaScript
   - layout/styling problem -> CSS
   - saved data / rules problem -> Python

6. Change one thing at a time.
7. Reload and verify.

## Project-Specific Shortcuts

These files are the most common places to look first:

### Public site

- `templates/index.html`
- `static/js/booking.js`
- `static/js/modals.js`
- `static/css/booking.css`
- `static/css/modals.css`
- `static/css/home.css`

### Admin site

- `templates/admin.html`
- `static/js/admin_dashboard.js`
- `static/css/admin.css`

### Backend logic

- `app/routes.py`
- `app/util/booking_groups.py`
- `app/util/db_models.py`

## Useful Search Commands

Run these from the project root.

Search for a class name:

```bash
grep -RIn "booking-summary-item-line" templates static app
```

Search for visible button text:

```bash
grep -RIn "Lägg till en person" templates static app
```

Search only in JavaScript:

```bash
grep -RIn "Namn saknas" static/js
```

Search only in CSS:

```bash
grep -RIn "admin-inline-link" static/css
```

## Beginner Tip

Do not try to understand the whole repo at once.

For one UI issue, only answer these questions:

1. Where does this element get created?
2. Where does its data come from?
3. Where does its styling come from?

That is usually enough to make a correct small change.

## Three Real Examples From This Project

These examples show the difference between:

1. a template-driven element
2. a JavaScript-generated element
3. a CSS-only styling fix

### 1. Template-Driven Element

Example:

```html
<h2 id="publicSitePasswordPanelTitle">Byt gemensamt lösenord</h2>
```

Why this is template-driven:

- this heading exists immediately when the admin page loads,
- it is static text,
- it belongs to the HTML structure of the modal.

Where to change it:

- [admin.html](/home/marcgust/workspace/github.com/Marcus-Gustafsson/Paddling/templates/admin.html)

How to find it:

1. Inspect the heading in the browser.
2. Copy either:
   - the text `Byt gemensamt lösenord`
   - or the id `publicSitePasswordPanelTitle`
3. Search:

```bash
grep -RIn "publicSitePasswordPanelTitle" templates static app
```

or:

```bash
grep -RIn "Byt gemensamt lösenord" templates static app
```

Why this search works:

- ids and static headings are usually defined directly in a template.

### 2. JavaScript-Generated Element

Example:

```html
<span class="booking-summary-item-line">?</span>
```

Why this is JavaScript-generated:

- the booking summary is built after the user interacts with the booking form,
- that means the browser does not receive those summary rows directly from the
  server,
- JavaScript creates them in the page after the user selects canoes and types
  names.

Where to change it:

- [booking.js](/home/marcgust/workspace/github.com/Marcus-Gustafsson/Paddling/static/js/booking.js)

How to find it:

1. Inspect the element.
2. Copy the class name:

```html
booking-summary-item-line
```

3. Search:

```bash
grep -RIn "booking-summary-item-line" templates static app
```

4. Notice:
   - `static/js/booking.js` creates the element
   - `static/css/booking.css` styles the element

How to change `?` to `Namn saknas`:

In [booking.js](/home/marcgust/workspace/github.com/Marcus-Gustafsson/Paddling/static/js/booking.js), find:

```js
const secondRiderName = buildFullName(..., "?");
```

and change the fallback string to:

```js
"Namn saknas"
```

### 3. CSS-Only Styling Fix

Example:

You inspect a button and the structure is correct, but it still shows when it
should be hidden.

In this project, one example is the admin inline links:

```html
<button class="admin-inline-link" hidden>...</button>
```

Why this is a CSS-only fix:

- the HTML is correct
- the JavaScript is already toggling the `hidden` attribute
- the visual problem comes from the styling layer

Where to change it:

- [admin.css](/home/marcgust/workspace/github.com/Marcus-Gustafsson/Paddling/static/css/admin.css)

What the fix looks like:

```css
.admin-inline-link[hidden] {
  display: none !important;
}
```

How to find it:

1. Inspect the broken button.
2. Look at the class name:

```html
admin-inline-link
```

3. Search:

```bash
grep -RIn "admin-inline-link" templates static app
```

4. You will usually find:
   - the button markup in `templates/admin.html`
   - the behavior in `static/js/admin_dashboard.js`
   - the styling in `static/css/admin.css`

If the structure and behavior are already correct, the remaining fix is often
CSS.

## Easy Navigation In Zed And VS Code

If you are mainly using Zed or VS Code, use the editor search tools first and
the terminal search second.

### Best starting point

When you inspect an element, copy one of these:

1. the class name
2. the id
3. the visible text
4. a `data-*` attribute

Then search that exact string in the editor.

### Zed tips

Useful shortcuts:

- `Ctrl+Shift+F`
  Search across the whole project
- `Ctrl+P`
  Open a file quickly by name
- `Ctrl+F`
  Search inside the current file

Simple workflow in Zed:

1. Inspect the element in the browser.
2. Copy the class name, for example:

```text
booking-summary-item-line
```

3. Press `Ctrl+Shift+F`.
4. Paste the class name.
5. Open the matching result in:
   - `templates/`
   - `static/js/`
   - `static/css/`

Tip:

- if the same class appears in both JS and CSS, the JS usually creates it and
  the CSS styles it.

### VS Code tips

Useful shortcuts:

- `Ctrl+Shift+F`
  Search across the whole project
- `Ctrl+P`
  Open a file quickly
- `Ctrl+F`
  Search inside the current file
- `Alt+Click`
  Place multiple cursors for small repetitive edits

Simple workflow in VS Code:

1. Open global search with `Ctrl+Shift+F`.
2. Paste the class name or text from the browser.
3. Start with the most specific result.
4. If you are not sure which file is correct:
   - `templates/` means HTML structure
   - `static/js/` means behavior or generated content
   - `static/css/` means styling

### When editor search is better than terminal search

Use editor search first when:

- you want clickable results
- you want to jump between files quickly
- you want to compare template, JS, and CSS matches side by side

### When terminal search is better

Use terminal search when:

- you want exact control over the search
- you want to search only certain folders
- you want a fast overview from the project root

Example:

```bash
grep -RIn "booking-summary-item-line" templates static app
```

## Practical Beginner Routine

For each UI change, follow this order:

1. Inspect the element in the browser.
2. Search the class name or text in Zed or VS Code.
3. Decide:
   - template
   - JavaScript
   - CSS
   - backend
4. Change one small thing.
5. Reload and verify.
6. Repeat only if needed.

This is the safest way to learn the codebase without getting lost.
