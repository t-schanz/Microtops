from .DataHandling import read_image
import cv2
from datetime import datetime as dt
import numpy as np
import collections
import pysolar
from .DShipHandling import recieve_data
import pytz
import logging


class ImageProcessor(object):

    def __init__(self):

        self.height = 0
        self.image = None
        self.image_mask = None

        self.angle_array = None
        self.mask_around_sun = None

        self.lat = None
        self.lon = None
        self.pitch = None
        self.roll = None
        self.heading = None

        self.date = None

    def get_cloudiness_status(self, image_path, coverage_thresh=0.5):
        """
        Returns 0 if there are clouds around the sun.
        Returns 1 if there are no clouds around the sun.

        Args:
            image_path: str: path and name of the cloud image
            date: datetime.datetime object
        """

        self.read_dship_data()
        image = read_image(image_path)
        image = self.make_image_square(image)
        image = self._rotate_image(image, self.heading)
        self.image = image
        self.crop_image(image, elevation=0)
        self.get_sun_position()
        self.remove_sun()
        self.cloud_mask = self.create_cloud_mask(image)
        self.get_sun_square()
        # sun_position = self.find_sun_position(image, lat, lon, pitch, roll)
        coverage = self._calculate_coverage()
        if coverage < coverage_thresh:
            return 1
        else:
            return 0

    def _calculate_coverage(self):
        mask = self.mini_mask.copy()
        cloud_pixels = len(np.where(mask == 1)[0])
        sky_pixels = len(np.where(mask == 0)[0])
        logging.debug(f"cloud_pixel: {cloud_pixels} | sky_pixel: {sky_pixels}")

        coverage = cloud_pixels /(cloud_pixels + sky_pixels)

        return coverage

    def make_image_square(self, image: np.ndarray) -> np.ndarray:
        x, y = self.find_center(image)
        width = image.shape[1]
        height = image.shape[0]

        if height < width:
            square_image = image[:, x - int(height / 2):x + int(height / 2)]
        else:
            square_image = image[y - int(width / 2):y + int(height / 2), :]

        return square_image

    @staticmethod
    def find_center(image):
        """
        Find the position (x,y) of the center of an array.

        Returns: tuple: center of the image.
        """
        center_x = int(np.divide(image.shape[1], 2))
        center_y = int(np.divide(image.shape[0], 2))

        return center_x, center_y

    def read_dship_data(self) -> (float, float, float, float):
        data = recieve_data()
        self.lat = data["lat"]
        self.lon = data["lon"]
        self.heading = data["heading"]
        self.date = dt.strptime(data["date"], "%Y%m%d%H%M%S").replace(tzinfo=pytz.UTC)

    def find_sun_position(self, image, lat, lon, pitch, roll) -> (float, float):
        pass
        # return(x, y)

    def rotate_image(self, image, deg):
        """
        Uses the mathematical rotation of a matrix by creating a rotation-matrix M
        to rotate the image by a certain degree.

        The result is stored as class-variable self.rotated

        Args:
            image: np.ndarray
            deg: degree (in meteorological direction) for the image to be rotated
        """
        rows, cols = self.get_image_size(image)
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), -deg, 1)
        return cv2.warpAffine(image, M, (cols, rows))

    @staticmethod
    def get_image_size(image):
        """
        get the length along both axes of the input image.

        Returns:
            tuple of (x_size, y_size)
        """
        x_size = image.shape[0]
        y_size = image.shape[1]

        return x_size, y_size

    def create_cloud_mask(self, image) -> np.ndarray:
        """
        Creates an array self.cloud_image where clouds are masked, based on some
        sky index (SI) and brightness index (BI).
        Furthermore creates the self.cloud_mask.

        The algorithm works, by comparing pixel values relative to each other and
        setting pixel to be a "cloud", when a certain threshold is met:
         >>> mask_sol1 = SI < 0.12

        In the area around the sun, where "sun-glare" at the lense is present, this
        threshold is set dynamically dependent on the distance between each pixel and
        the sun.
        """

        image_f = image.astype(float)
        # image_f = self.crop_image(image_f,elevation=5)

        SI = ((image_f[:, :, 2]) - (image_f[:, :, 0])) / (
            ((image_f[:, :, 2]) + (image_f[:, :, 0])))

        SI[np.isnan(SI)] = 1

        mask_sol1 = SI < 0.18

        x_sol_cen, y_sol_cen = self.ele_azi_to_pixel(self.sun_azimuth, self.sun_elevation)
        x_size, y_size = self.get_image_size(image)
        y, x = np.ogrid[-y_sol_cen:y_size - y_sol_cen, -x_sol_cen:x_size - x_sol_cen]

        size = 50
        radius_sol_area = size * 9
        sol_mask_area = x ** 2 + y ** 2 <= radius_sol_area ** 2
        new_mask = np.logical_and(~sol_mask_area, mask_sol1)

        cloud_image = image.copy()
        cloud_image[:, :, :][new_mask] = [255, 0, 0]
        cloud_mask = cloud_image[:, :, 0].copy()
        cloud_mask[:, :][np.where(cloud_mask != 0)] = 2
        cloud_mask[:, :][self.mask_around_sun] = 0
        cloud_mask[:, :][new_mask] = 1

        Radius_sol = 100
        sol_mask_cen = x ** 2 + y ** 2 <= Radius_sol ** 2

        # AREA AROUND SUN:
        parameter = np.zeros(size)
        for j in range(size):
            parameter[j] = (0 + j * 0.4424283716980435 - pow(j, 2) * 0.06676211439554262 + pow(j, 3) *
                            0.0026358061791573453 - pow(j, 4) * 0.000029417130873311177 + pow(j, 5) *
                            1.0292852149593944e-7) * 0.001

        for j in range(size):
            Radius_sol = j * 10
            sol_mask = (x * x) + (y * y) <= Radius_sol * Radius_sol
            mask2 = np.logical_and(~sol_mask_cen, sol_mask)
            sol_mask_cen = np.logical_or(sol_mask, sol_mask_cen)

            mask3 = SI < parameter[j] + 0.08
            mask3 = np.logical_and(mask2, mask3)
            # image_array_c[mask3] = [255, 0, 0]
            cloud_image[mask3] = [255, 255 - 3 * j, 0]
            cloud_mask[mask3] = 1

        return cloud_mask

    def remove_sun(self):
        """
        Calculates the center of the sun inside the image
        and draws a circle around it.

        """

        if not isinstance(self.angle_array, collections.Iterable):
            self.create_angle_array()

        # sun_pos = self.find_nearest_idx(self.angle_array[:, :, 0], self.angle_array[:, :, 1],
        #                                 self.sun_azimuth, self.sun_elevation)

        # -----------Draw circle around position of sun--------------------------------------------------------------

        # x_sol_cen, y_sol_cen = sun_pos
        x_sol_cen, y_sol_cen = self.ele_azi_to_pixel(self.sun_azimuth, self.sun_elevation)

        # print("X_SOL_CEN", x_sol_cen, y_sol_cen)
        Radius_sol = 100
        Radius_sol_center = 0

        x_size, y_size = self.get_image_size(self.image)

        y, x = np.ogrid[-y_sol_cen:y_size - y_sol_cen, -x_sol_cen:x_size - x_sol_cen]
        sol_mask = x ** 2 + y ** 2 <= Radius_sol ** 2
        sol_mask_cen = x ** 2 + y ** 2 <= Radius_sol_center ** 2
        sol_mask_cen1 = np.logical_xor(sol_mask_cen, sol_mask)
        self.image[:, :, :][sol_mask_cen1] = [0, 0, 0]

        self.image_mask = np.logical_xor(self.image_mask, sol_mask_cen1)
        self.mask_around_sun = sol_mask_cen1

    def crop_image(self, image, elevation=30, crop_value=0):
        """
        Crops the image, so that only the center is being used.
        An elevation angle of 30 would mean, that everything below 30 degrees
        elevation will be cut away, leaving an opening angle of 120 degrees.

        Args:
            elevation: Angle at which the image will be cut.

        """

        x_center, y_center = self.find_center(self.image)
        x_size, y_size = self.get_image_size(self.image)
        y, x = np.ogrid[-y_center:y_size - y_center, -x_center:x_size - x_center]

        crop_size = x_size / 2 - (x_size / 2 / 90 * elevation)

        center_mask = x ** 2 + y ** 2 <= (crop_size) ** 2

        # print("DIMENSION: ", np.ndim(image))
        if np.shape(image)[2] == 3:
            image[:, :, :][~center_mask] = [crop_value, crop_value, crop_value]
        elif np.shape(image)[2] == 2:
            # print("Cropping image!")
            image[:, :][~center_mask] = [crop_value, crop_value]
        elif np.ndim(image) == 2:
            # print("Cropping image!")
            image[:, :][~center_mask] = crop_value
        else:
            raise IndexError("For this index the cropping is not implemented yet.")

        self.image_mask = center_mask

        return image

    def create_angle_array(self):
        """
        Creates an array in which the azimuth and elevation angles are the values
        The 0 dimension is th azimuth
        The 1 dimension is the elevation

        The values are for a theoretically perfect alligned and turned image!

        Examples:
            To get the elevation over the whole allskyimage :

            >>> plt.imshow(self.angle_array[:,:,1])



        Returns:
            sets the self.angle_array

        """
        x_size, y_size = self.get_image_size(self.image)

        angle_array = np.zeros([x_size, y_size, 2])

        xx, yy = np.meshgrid(range(x_size), range(y_size), sparse=True)

        x_dash = self._convert_var_to_dash(xx)
        y_dash = self._convert_var_to_dash(yy)

        # Azimuth angle:
        angle_array[xx, yy, 0] = self._azimuth_angle(x_dash, y_dash) + self.heading
        angle_array[:, :, 0] = np.subtract(angle_array[:, :, 0], 90)
        negative_mask = angle_array[:, :, 0] < 0
        angle_array[:, :, 0][negative_mask] = np.add(angle_array[:, :, 0][negative_mask], 360)
        angle_array = np.fliplr(angle_array)

        # Elevation angle:
        angle_array[xx, yy, 1] = self._elevation_angle(x_dash, y_dash)
        angle_array[:, :, 1] = np.subtract(angle_array[:, :, 1], 90)
        angle_array[:, :, 1] = np.negative(angle_array[:, :, 1])

        self.angle_array = angle_array

    def ele_azi_to_pixel(self, azimuth, elevation):

        """
        Converts an azimuth and elevation angle to the position of the pixel
        inside the image.

        Args:
            azimuth: azimuth angle
            elevation: elevation angle

        Returns:

        """
        x_size, y_size = self.get_image_size(self.image)

        r = x_size / 2 * (1 - ((90 - elevation) / 90))

        x = r * np.sin(np.deg2rad(azimuth)) + x_size / 2
        y = r * np.cos(np.deg2rad(azimuth)) + x_size / 2

        return int(round(x, 0)), int(round(y, 0))

    def pixel_to_ele_azi(self, x, y):
        """
        Method to get the azimuth and elevation of a single allsky-image pixel.

        Args:
            x: position pixel in x direction
            y: position pixel in y direction

        Returns:
            tuple of (azimuth, elevation)
        """

        x_dash = self._convert_var_to_dash(x)
        y_dash = self._convert_var_to_dash(y)

        azimuth = self._azimuth_angle(x_dash, y_dash)
        if azimuth < 0:
            azimuth += 360

        elevation = self._elevation_angle(x_dash, y_dash)
        elevation -= 90
        elevation *= -1

        return azimuth, elevation

    def _convert_var_to_dash(self, var):
        """
        This function converts a variable x or y to be dependent on the center:

            x' = x - a
            y* = y - a

        Args:
            var: x or y

        Returns: x' or y'

        """
        a = self.get_image_size(self.image)[0] / 2
        return var - a

    @staticmethod
    def _azimuth_angle(x_dash, y_dash):
        """
        calculates the azimuth angle in the picture from coordinates x' and y'


        Args:
            x_dash: x'
            y_dash: y'

        Returns:
            azimuth angle alpha of the coordinates x' and y'.

        """
        return np.rad2deg(np.arctan2(x_dash, y_dash))

    def _elevation_angle(self, x_dash, y_dash):
        """
        calculates the elevation angle in the picture from coordinates x' and y'

        Args:
            x_dash: x'
            y_dash: y'

        Returns:
            elevation angle epsilon of the coordinates x' and y'.

        """
        a = self.get_image_size(self.image)[0] / 2
        r = self._calc_radius(x_dash, y_dash)

        return np.multiply(90, (1 - np.divide(r, a)))

    @staticmethod
    def _calc_radius(x, y):
        """
        calculates the radius from x and y:

        r = sqrt(x² + y²)

        Args:
            x:
            y:

        Returns:
            radius r.
        """
        return np.sqrt(np.power(x, 2) + np.power(y, 2))

    def get_sun_position(self):
        """
        Calculates the theoretic position of the sun by the lon, lat height and
        date of the image.

        """

        sun_elevation = pysolar.solar.get_altitude(latitude_deg=self.lat, longitude_deg=self.lon,
                                                   when=self.date, elevation=self.height)

        sun_elevation = 90 - sun_elevation
        self.sun_elevation = sun_elevation

        sun_azimuth = pysolar.solar.get_azimuth(latitude_deg=self.lat, longitude_deg=self.lon,
                                                when=self.date, elevation=self.height)

        if sun_azimuth < 0:
            if (sun_azimuth >= -180):
                solarheading = ((sun_azimuth * -1) + 180)
            if (sun_azimuth < -180):
                solarheading = ((sun_azimuth * -1) - 180)
            if sun_azimuth >= 0:
                solarheading = sun_azimuth
        else:
            solarheading = sun_azimuth

        self.sun_azimuth = solarheading

    def _rotate_image(self, image, deg):
        """
        Uses the mathematical rotation of a matrix by creating a rotation-matrix M
        to rotate the image by a certain degree.

        The result is stored as class-variable self.rotated

        Args:
            deg: degree (in meteorological direction) for the image to be rotated
        """
        rows, cols = self.get_image_size(image)
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), -deg, 1)
        self.rotated = cv2.warpAffine(image, M, (cols, rows))
        return self.rotated

    def get_sun_square(self, size=600):
        x_sol_cen, y_sol_cen = self.ele_azi_to_pixel(self.sun_azimuth, self.sun_elevation)


        x_size, y_size = self.get_image_size(self.image)

        mini_image = np.empty((size, size, 3))
        mini_mask = np.empty((size, size))

        self.mini_image = self.image[(y_sol_cen-int(size/2)):(y_sol_cen+int(size/2)),
                          (x_sol_cen - int(size / 2)):(x_sol_cen + int(size / 2)), :]
        self.mini_mask = self.cloud_mask[(y_sol_cen-int(size/2)):(y_sol_cen+int(size/2)),
                          (x_sol_cen - int(size / 2)):(x_sol_cen + int(size / 2))]


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    file = "C:/Users/darkl/PycharmProjects/Microtops/data/m190530211401627.jpg"
    SkImager = ImageProcessor()
    date = dt(2019, 5, 30, 21, 14, 32)
    status = SkImager.get_cloudiness_status(file)

    # on linux:
    # import os
    # beep = lambda x: os.system("echo -n '\a';sleep 0.2;" * x)
    # beep(3)

    # on windows:
    import winsound
    if status:
        frequency = 600  # Set Frequency To 2500 Hertz
        duration = 1000  # Set Duration To 1000 ms == 1 second
        winsound.Beep(frequency, duration)
