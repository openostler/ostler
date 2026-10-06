// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import packJson from "../api/fixtures/pack.json";
import { PackSchema, type Pack } from "../api/schemas";

/** The real lr_d2 manifest (GET /pack, written from PACK.manifest()) as the tests' pack. */
export const packFixture: Pack = PackSchema.parse(packJson);
