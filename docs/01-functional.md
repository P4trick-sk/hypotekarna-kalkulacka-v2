# 01 – Functional Specification

## 1. Purpose

The Mortgage Calculator is a static web app that estimates what a home loan will cost: the monthly payment, the total interest, the payoff date and how extra payments change them. It runs entirely in the browser and needs no account or server.

## 2. User Story

> **As a** prospective home buyer,
> **I want to** enter the price of a home, my down payment, the interest rate and the loan term,
> **so that** I can see what I would pay each month, how much the loan costs in total, and how extra payments would shorten it, before I talk to a lender.

### Acceptance criteria

1. **Given** I open the app for the first time, **when** the page loads, **then** it shows a complete result for the default values (price 300,000, down payment 60,000, rate 4.5 %, term 30 years, tax 1,200/year, insurance 600/year, currency EUR, first payment next month).
2. **Given** I change any input, **when** I type or move a slider, **then** every result, chart and table updates straight away, with no submit button.
3. **Given** valid inputs, **then** I see the monthly total and its split into principal & interest, extra payment, and tax & insurance.
4. **Given** valid inputs, **then** I see the loan amount, total interest, total cost of the loan and the payoff date.
5. **Given** I enter an extra monthly payment greater than 0, **then** I see how much sooner the loan is paid off and how much interest I save compared with no extra payment.
6. **Given** I enter an invalid value (for example a down payment larger than the price), **then** I see a clear error message and the previous results are shown as out of date instead of being recalculated.
7. **Given** I close the app and open it again in the same browser, **then** my last inputs and chosen theme are restored.
8. **Given** I want to keep the numbers, **when** I click *Download CSV*, **then** I get the full monthly amortization schedule as a file.

## 3. Features

### F1 – Loan inputs

| Input | Format | Rules |
| --- | --- | --- |
| Home price | Amount, with slider (20,000 – 2,000,000) | Must be greater than 0 |
| Down payment | Amount **or** percentage, kept in sync; slider 0 – 100 % | 0 or more and less than the home price |
| Interest rate | Percentage, with slider (0 – 15 %) | 0 – 50 % |
| Loan term | Presets 10 / 15 / 20 / 25 / 30 years, or a custom value | Whole years, 1 – 50 |
| First payment | Month and year | Defaults to next month |
| Extra monthly payment *(optional)* | Amount, with slider (0 – 3,000) | 0 or more |
| Property tax / year *(optional)* | Amount | 0 or more |
| Insurance / year *(optional)* | Amount | 0 or more |

- Number fields accept both `250,000.50` and `250 000,50` styles, whatever the browser locale.
- Values are reformatted with thousands separators when a field loses focus.
- *Reset to defaults* restores every input to its default value.

### F2 – Validation

- Inputs are checked on every change. The first problem found is shown in a single error message (announced to screen readers).
- While there is an error, results are dimmed and not recalculated, and the invalid state is not saved.

### F3 – Payment calculation

- The monthly principal & interest uses the standard amortization formula `P × r / (1 − (1 + r)^−n)`, where `P` is the loan amount, `r` the monthly rate and `n` the number of payments. A 0 % rate divides the loan evenly over the term.
- Each month, interest is charged on the remaining balance and the rest of the payment, including any extra payment, reduces the principal.
- The final payment covers only what is left of the balance.
- Tax and insurance are divided by 12 and added to the monthly total. They do not affect the loan balance.

### F4 – Results summary

- **Monthly payment:** the total due each month, with a line splitting it into principal & interest, extra payment, and tax & insurance.
- **Payment breakdown bar:** shows the share of principal, interest, extra payment and tax & insurance in the first payment, with a legend.
- **Loan amount:** with the down payment percentage and loan-to-value ratio.
- **Total interest:** with interest as a percentage of the loan, or the amount saved when an extra payment is set.
- **Total cost of the loan:** principal plus interest.
- **Payoff date:** month and year of the last payment, the duration, and the number of payments.
- **"Sooner" badge:** when an extra payment shortens the loan, shows by how much (for example "4 years 3 months sooner").

### F5 – Charts

- **Remaining balance:** the balance over time. With an extra payment, the standard schedule is shown alongside for comparison.
- **Principal vs. interest by year:** a stacked column chart of how each year's payments split.
- Tooltips show exact values on hover, on keyboard focus, and when moving between points with the arrow keys.
- Charts redraw when the window is resized or the theme changes.

### F6 – Amortization schedule

- A table that can switch between a **yearly** and a **monthly** view, showing payment, principal, interest and remaining balance for each period, with dates.
- **Download CSV:** exports the full monthly schedule (payment number, date, payment amount, principal, interest, balance). The file name includes the currency, e.g. `mortgage-schedule-eur.csv`.

### F7 – Currency and formatting

- Currency selector: EUR, USD, GBP, CZK, CHF, PLN. Changing it updates symbols and amounts; it does not convert values.
- Numbers, currency and dates are formatted using the browser's locale.

### F8 – Theme

- Light and dark themes. The app follows the system setting by default and has a manual toggle; the chosen theme is remembered.

### F9 – Persistence

- Inputs, currency and theme are saved in the browser's local storage and restored on the next visit. Nothing is sent to a server.

### F10 – Accessibility and layout

- All controls have labels and can be used with the keyboard; term presets and the schedule view behave as radio groups.
- Charts and tooltips can be reached and read with the keyboard.
- The layout adapts to phone, tablet and desktop widths.

## 4. Out of scope

- Fees, PMI, closing costs and variable or changing interest rates.
- Currency conversion.
- User accounts, saving several scenarios, or sharing results.
- Results are estimates; a lender's figures may differ because of fees, rounding and rate changes.
