/** Land Rover Discovery 2 Td5 (pack "lr_d2"): the Drive views its layout.json names. */
import { registerViews } from "../registry";
import { BodyCar } from "./BodyCar";
import { SlabsCar } from "./SlabsCar";

export const PACK_ID = "lr_d2";

registerViews(PACK_ID, { slabs_car: SlabsCar, body_car: BodyCar });
