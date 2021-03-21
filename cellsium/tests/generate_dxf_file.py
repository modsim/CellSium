def generate_dxf_file(output_filename, line_type='LWPOLYLINE'):
    assert line_type in ('LWPOLYLINE', 'POLYLINE', 'SPLINE')

    x, y = 10, 10
    w, h = 20, 20

    lines = [
        [[x, y], [y, y + h]],
        [[x, y + h], [x + w, y + h]],
        [[x + w, y + h], [x + w, y]],
        [[x + w, y], [x, y]],
    ]

    import ezdxf

    dxf = ezdxf.new('R2010')

    modelspace = dxf.modelspace()

    if line_type == 'LWPOLYLINE':
        for line_points in lines:
            modelspace.add_lwpolyline(line_points)
    elif line_type == 'POLYLINE':
        for line_points in lines:
            modelspace.add_polyline2d(line_points)
    elif line_type == 'SPLINE':
        for line_points in lines:
            modelspace.add_spline(line_points)
    dxf.saveas(output_filename)


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:
        print(f"Usage: {sys.argv[0]} filename.dxf <LWPOLYLINE|POLYLINE|SPLINE>")
    elif len(sys.argv) == 2:
        generate_dxf_file(sys.argv[1])
    elif len(sys.argv) > 2:
        generate_dxf_file(sys.argv[1], sys.argv[2])
