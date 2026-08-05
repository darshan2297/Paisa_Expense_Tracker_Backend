# Changelog

## [1.1.0](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/compare/v1.0.0...v1.1.0) (2026-08-05)


### Features

* add payment_method on transactions ([f174e29](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/f174e29c4339a4b0e83bbb6c1051f858acf6f39a))
* send daily Resend email reminders until items are paid ([0194a84](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/0194a840a6d21da41ce39aca0eb90f1f96adddbd))


### Bug Fixes

* allow updating card outstanding via PATCH ([cfccd2c](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/cfccd2c241466e2562ac53a22f9614ed8dead812))
* card EMI field and exclude unpaid card spend from cash ([0865d68](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/0865d68887d05e8caaf10c6beef17c10a2aae814))
* compute budget days remaining in Asia/Kolkata ([790cf47](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/790cf471d1e497b054efcde85f29e91ba6b39100))
* compute loan EMI from outstanding and remaining term ([9e29105](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/9e2910521b89165cad1d045c9ac277e1d8180d31))
* expand loan PATCH fields for full edit support ([f368afd](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/f368afd1d43d7fafac154b49e1df819f21fcde40))
* include unpaid bills when listing by month ([96c5bc8](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/96c5bc85346d6beb5b1d553c0c40dc39cc9247e5))
* make remote device sign-out invalidate that client's JWTs ([fd4bc1c](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/fd4bc1c33ddbb2777e8215c7db52fa6eecef9e55))
* mirror people ledger settle-ups into cash transactions ([3fee51a](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/3fee51a5a63f72a6a255b5a67e1d7cfa4603dff6))
* scale report chart bars to fit the chart track ([311450b](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/311450b7f28d7a26732128673384e7e623249b56))
* stop injecting loan EMIs into the cash flow calendar ([a19ee8f](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/a19ee8fd84a4b0e775bb703088a254b71dd2e6b7))

## 1.0.0 (2026-08-04)


### Features

* **auth:** F1 - auth + user profile API ([60976c8](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/60976c8ddc5684e690bc23b46bf3b0eb10311f8e))
* F2-F6 API modules and backend platform stack ([e3ebece](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/e3ebece8c35a43d139c12cd78d9a982a03d2b5be))
* F7-F20 core platform modules (goals through security/app-lock) ([e578a3e](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/e578a3edc5bbaf560b09f02c053504aaedf0e93a))


### Bug Fixes

* make release/v1.0.0 pass CI lint and bills date assertion ([b2271ea](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/b2271ea32f390b038ee058e42937b9eba316e453))
* pin ruff to a version supporting UP046/UP047, commit poetry.lock ([6913c41](https://github.com/darshan2297/Paisa_Expense_Tracker_Backend/commit/6913c410e3f76d8148b6982512090a3ca844dc69))
