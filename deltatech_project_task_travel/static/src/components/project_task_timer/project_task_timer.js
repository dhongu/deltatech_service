import { ProjectTaskFormController } from "@project/views/project_task_form/project_task_form_controller";
import { projectTaskFormView } from "@project/views/project_task_form/project_task_form_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class TravelProjectTaskFormController extends ProjectTaskFormController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    async beforeExecuteActionButton(clickParams) {
        if (["action_travel_start", "action_travel_stop", "action_timer_start"].includes(clickParams.name)) {
            const success = await this.captureAndSaveLocation(clickParams.name);
            if (success && clickParams.name !== "action_timer_start") {
                return false; // Prevent Odoo from calling the method again without coords
            }
        }
        return super.beforeExecuteActionButton(...arguments);
    }

    async captureAndSaveLocation(method) {
        if (navigator.geolocation) {
            return new Promise((resolve) => {
                navigator.geolocation.getCurrentPosition(
                    async (pos) => {
                        const coords = {
                            lat: pos.coords.latitude,
                            lng: pos.coords.longitude
                        };
                        try {
                            if (method === "action_timer_start") {
                                await this.orm.call("project.task", "write", [
                                    [this.model.root.resId],
                                    {
                                        travel_stop_latitude: coords.lat,
                                        travel_stop_longitude: coords.lng,
                                    }
                                ]);
                            } else {
                                await this.orm.call("project.task", method, [
                                    [this.model.root.resId],
                                    coords
                                ]);
                            }

                            if (["action_travel_start", "action_travel_stop", "action_timer_start"].includes(method)) {
                                await this.model.root.load();
                            }
                        } catch (err) {
                            console.error("Error saving location:", err);
                        }
                        resolve(true);
                    },
                    (err) => {
                        console.warn("GPS error:", err);
                        this.notification.add("Could not capture GPS location.", { type: "warning" });
                        resolve(false);
                    },
                    { enableHighAccuracy: true, timeout: 5000 }
                );
            });
        }
        return false;
    }
}

registry.category("views").add("travel_project_task_form", {
    ...projectTaskFormView,
    Controller: TravelProjectTaskFormController,
});
