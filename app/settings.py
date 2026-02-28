import yaml
import os

class Settings:
    def __init__(self, config_file):
        self.config_file = config_file
        self.load()

    def default_get(self, data, name, default):
        try:
            return data.get(name, default)
        except:
            return default

    def load(self):
        try:
            with open(self.config_file, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader) or {}
        except:
            data = {}

        # ───────────────────────────────────────────────
        # UI & Server Preferences
        # ───────────────────────────────────────────────
        self.selected_theme     = self.default_get(data, 'selected_theme', "Default")
        self.server_name        = self.default_get(data, 'server_name', "")
        self.server_port        = self.default_get(data, 'server_port', 0)
        self.server_share       = self.default_get(data, 'server_share', False)
        self.launch_browser     = self.default_get(data, 'launch_browser', False)

        # ───────────────────────────────────────────────
        # Output & File Handling
        # ───────────────────────────────────────────────
        self.output_image_format   = self.default_get(data, 'output_image_format', 'png')
        self.output_video_format   = self.default_get(data, 'output_video_format', 'mp4')
        self.output_video_codec    = self.default_get(data, 'output_video_codec', 'libx264')
        self.video_quality         = self.default_get(data, 'video_quality', 14)
        self.output_template       = self.default_get(data, 'output_template', '{file}_{time}')
        self.use_os_temp_folder    = self.default_get(data, 'use_os_temp_folder', False)
        self.output_show_video     = self.default_get(data, 'output_show_video', True)
        self.clear_output          = self.default_get(data, 'clear_output', True)

        # ───────────────────────────────────────────────
        # Performance & Execution
        # ───────────────────────────────────────────────
        self.max_threads    = self.default_get(data, 'max_threads', 2)
        self.memory_limit   = self.default_get(data, 'memory_limit', 0)
        self.provider       = self.default_get(data, 'provider', 'cuda')
        self.force_cpu      = self.default_get(data, 'force_cpu', False)

        # ───────────────────────────────────────────────
        # Faceswap & Quality Controls
        # ───────────────────────────────────────────────
        self.max_face_distance     = self.default_get(data, 'max_face_distance', 0.65)
        self.blend_ratio           = self.default_get(data, 'blend_ratio', 0.65)
        self.selected_enhancer     = self.default_get(data, 'selected_enhancer', "None")
        self.mask_erosion          = self.default_get(data, 'mask_erosion', 1.0)
        self.mask_blur             = self.default_get(data, 'mask_blur', 20.0)
        self.num_swap_steps        = self.default_get(data, 'num_swap_steps', 1)
        self.autorotate            = self.default_get(data, 'autorotate', True)
        self.skip_audio            = self.default_get(data, 'skip_audio', False)
        self.preview_swap_enabled  = self.default_get(data, 'preview_swap_enabled', False)
        self.selected_mask_engine  = self.default_get(data, 'selected_mask_engine', "None")
        self.subsample_upscale     = self.default_get(data, 'subsample_upscale', "128px")

    def save(self):
        data = {
            # UI & Server
            'selected_theme': self.selected_theme,
            'server_name': self.server_name,
            'server_port': self.server_port,
            'server_share': self.server_share,
            'launch_browser': self.launch_browser,

            # Output & File Handling
            'output_image_format': self.output_image_format,
            'output_video_format': self.output_video_format,
            'output_video_codec': self.output_video_codec,
            'video_quality': self.video_quality,
            'output_template': self.output_template,
            'use_os_temp_folder': self.use_os_temp_folder,
            'output_show_video': self.output_show_video,
            'clear_output': self.clear_output,

            # Performance & Execution
            'max_threads': self.max_threads,
            'memory_limit': self.memory_limit,
            'provider': self.provider,
            'force_cpu': self.force_cpu,

            # Faceswap & Quality
            'max_face_distance': self.max_face_distance,
            'blend_ratio': self.blend_ratio,
            'selected_enhancer': self.selected_enhancer,
            'mask_erosion': self.mask_erosion,
            'mask_blur': self.mask_blur,
            'num_swap_steps': self.num_swap_steps,
            'autorotate': self.autorotate,
            'skip_audio': self.skip_audio,
            'preview_swap_enabled': self.preview_swap_enabled,
            'selected_mask_engine': self.selected_mask_engine,
            'subsample_upscale': self.subsample_upscale,
        }

        os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(data, f, sort_keys=False)