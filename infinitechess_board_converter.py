import itertools
import copy
import collections
from collections import deque
import math

def convert_board_notation_to_long_format(board):
    """turn ICN format into a dictionary"""
    new_board = board.split()[-1]
    new_board = new_board.split("|")
    infinite_board_pieces = {}
    for piece in new_board:
        piece = piece.replace(" ", "")
        if piece[-1] == "+":
            piece = piece[:-1]
        infinite_board_pieces.update({tuple(int(coord) - 4.5
                                      for coord in piece[1:].split(",")): piece[0]})
    return infinite_board_pieces

def convert_long_format_to_board_notation(infinite_board_pieces):
    """turn the disctionary into ICN format"""
    new_board = """[Event "Casual local Classical infinite chess game"] [Site "https://www.infinitechess.org/"] [Variant "Classical"] [Round "-"] [UTCDate "2025.01.01"] [UTCTime "23:34:48"] [TimeControl "-"]  w 0/100 1 (8|1) """
    for piece, piece_type in infinite_board_pieces.items():
        new_board += piece_type +f"{piece[0]},{piece[1]}|"
    return new_board[:-1]


def create_groups():
    """assign to each piece a group, two pieces being in the same group
    if they are less that 5 squares away"""
    list_group = []
    list_mid_point = []
    list_moved_piece = set()

    for piece_coords, piece_type in infinite_board_pieces.items():
        if piece_coords not in list_moved_piece:
            list_group.append({piece_coords: piece_type})
            list_mid_point.append([[piece_coords[0]], [piece_coords[1]]])
            list_moved_piece.add(piece_coords)
            spread_group(piece_coords, list_group[-1], list_mid_point[-1], list_moved_piece)

    create_main_group(list_group, list_mid_point)
    print(list_group)
    print("first", list_mid_point)
    list_mid_point = [[sum(mid_point[0])/len(mid_point[0]),
                       sum(mid_point[1])/len(mid_point[1])]
                      for mid_point in list_mid_point]

    return list_group, list_mid_point


def spread_group(piece_coords, list_group, list_mid_point, list_moved_piece):
    list_close_move = [(i, j) for i in range(-5, 6) for j in range(-5, 6) if abs(i) + abs(j) <= 5]
    list_current_piece = deque([piece_coords])
    while list_current_piece:
        current_piece = list_current_piece.popleft()
        for move in list_close_move:
            square = (current_piece[0] + move[0], current_piece[1] + move[1])
            if (square in infinite_board_pieces.keys() and square not in list_moved_piece):
                list_current_piece.append(square)
                list_moved_piece.add(square)
                list_group.update({square: infinite_board_pieces[square]})
                list_mid_point[0].append(square[0])
                list_mid_point[1].append(square[1])


def create_main_group(list_group, list_mid_point):
    """combine the groups containing pawns to create the main group"""
    main_group = {}
    main_group_mid_point = [[],[]]
    for group, mid_point in zip(list_group.copy(), list_mid_point.copy()):
        if any(piece_type == "P" or piece_type == "p" for piece_type in group.values()):
            main_group.update(group)
            list_group.remove(group)
            main_group_mid_point[0] += mid_point[0]
            main_group_mid_point[1] += mid_point[1]
            list_mid_point.remove(mid_point)

    if len(main_group) != 0:
        list_group.insert(0, main_group)
        list_mid_point.insert(0, main_group_mid_point)


def furthest_pieces():
    """determine the furthest pieces in each direction to make the boundaries
    of the lines of sight"""
    list_group_direction = []
    for id_group, group in enumerate(list_group):
        list_piece_direction = [[], [], [], []]
        for piece in group.keys():
            list_piece_direction[0].append(piece[0])            # |
            list_piece_direction[1].append(piece[1])            # -
            list_piece_direction[2].append(piece[0] + piece[1]) # down \ up
            list_piece_direction[3].append(piece[0] - piece[1]) # up / down

        list_group_direction.append([[min(list_piece_direction[0]) - GROUP_PADDING,
                                      max(list_piece_direction[0]) + GROUP_PADDING],
                                     [min(list_piece_direction[1]) - GROUP_PADDING,
                                      max(list_piece_direction[1]) + GROUP_PADDING],
                                     [min(list_piece_direction[2]) - GROUP_PADDING / sqrt2,
                                      max(list_piece_direction[2]) + GROUP_PADDING / sqrt2],
                                     [min(list_piece_direction[3]) - GROUP_PADDING / sqrt2,
                                      max(list_piece_direction[3]) + GROUP_PADDING / sqrt2]])
    return list_group_direction




def create_links():
    """search for links between the groups (through queen moves),
    and relative positions in respect to the same lines of sights"""
    list_links = collections.defaultdict(dict)
    list_relative_position = collections.defaultdict(lambda: collections.defaultdict(dict))
    list_linked_group = collections.defaultdict(set)
    list_linked_group_per_direction = collections.defaultdict(lambda: [set(), set(), set(), set()])
    list_graph_branches = [{id_group} for id_group in range(len(list_group_direction))]
    list_offset = collections.defaultdict(lambda: collections.defaultdict(dict))

    list_axis = [[mid_point[0],
                  mid_point[1],
                  mid_point[0] + mid_point[1],
                  mid_point[0] - mid_point[1]]
                 for mid_point in list_mid_point]
    list_old_group_direction = copy.deepcopy(list_group_direction)
    for id_group, list_direction in enumerate(list_old_group_direction):

        for id_other_group, list_other_direction in enumerate(list_old_group_direction):
            if id_group == id_other_group:
                continue
            first_direction = None
            for id_direction in range(4):
                direction = list_direction[id_direction]
                other_direction = list_other_direction[id_direction]
                if other_direction[0] < direction[0] and other_direction[1] < direction[0]:
                    """the other group is on the bottom of the current group"""
                    list_relative_position[id_group][id_other_group].update({id_direction: -1})


                elif other_direction[0] > direction[1] and other_direction[1] > direction[1]:
                    """the other group is on the top of the current group"""
                    list_relative_position[id_group][id_other_group].update({id_direction: 1})

                else:
                    """the other group is in the line of sight of the current group"""
                    if first_direction != None and id_direction != first_direction:
                        """if there are two directions between the two mid points"""
                        merge_group(id_group, id_other_group)
                        return (True, ) * 8
                    first_direction = id_direction
                    list_links[id_group][id_other_group] = id_direction
                    list_linked_group[id_group].add(id_other_group)
                    list_linked_group_per_direction[id_group][id_direction].add(id_other_group)
                    list_offset[id_group][id_other_group] = (list_axis[id_group][id_direction] -
                                                             list_axis[id_other_group][id_direction])
                    list_graph_branches.append({id_group, id_other_group})


        if len(list_links[id_group]) != 0:
            if len({0, 1}.intersection(list_links[id_group].keys())) != 0:
                for id_other_direction in [2, 3]:
                    if id_other_direction in list_links[id_group].keys():
                        continue
                    length_increase = (OFFSET_COEFF * sum(abs(list_offset[id_group][id_linked_group])
                                                          for id_linked_group in {0, 1}.intersection(
                                                                  list_links[id_group].keys())))

                    list_group_direction[id_group][id_other_direction][0] -= length_increase
                    list_group_direction[id_group][id_other_direction][1] += length_increase

            if len({2, 3}.intersection(list_links[id_group].keys())) != 0:
                for id_other_direction in [0, 1]:
                    if id_other_direction in list_links[id_group].keys():
                        continue
                    length_increase = (OFFSET_COEFF * sum(abs(list_offset[id_group][id_linked_group])
                                                          for id_linked_group in {2, 3}.intersection(
                                                            list_links[id_group].keys())))/sqrt2

                    list_group_direction[id_group][id_other_direction][0] -= length_increase
                    list_group_direction[id_group][id_other_direction][1] += length_increase



    """connect all branches together to create graphs"""
    list_graph = []
    for branch in list_graph_branches:
        for graph in list_graph.copy():
            if not graph.isdisjoint(branch):
                branch.update(graph)
                list_graph.remove(graph)
        list_graph.append(branch)

    list_mid_point_graph = {id_mid_point: graph
                            for id_mid_point in range(len(list_mid_point))
                            for graph in list_graph
                            if id_mid_point in graph}

    return (False, list_links, list_relative_position,
            list_linked_group, list_linked_group_per_direction,
            list_graph, list_mid_point_graph, list_offset)




def merge_group(id_group, id_other_group):
    """merge groups together"""
    if id_group > id_other_group:
        id_group, id_other_group = id_other_group, id_group
    print("old", list_group[id_group], list_group[id_other_group])
    new_group = {**list_group.pop(id_other_group), **list_group.pop(id_group)}
    print("new", new_group)
    new_mid_point = [sum(coords)/2
                     for coords in zip(list_mid_point.pop(id_other_group),
                                       list_mid_point.pop(id_group))]

    if "p" in new_group.values() or "P" in new_group.values():
        list_group.insert(0, new_group)
        list_mid_point.insert(0, new_mid_point)
    else:
        list_group.append(new_group)
        list_mid_point.append(new_mid_point)


def is_parallel_linked_direction():
    """detect if two linked mid point are connected to another mid point by the same direction"""
    for id_mid_point in range(len(list_mid_point)):
        for id_direction in range(4):
            if len(list_linked_group_per_direction[id_mid_point][id_direction]) >= 2:
                list_permutations = itertools.permutations(
                    list_linked_group_per_direction[id_mid_point][id_direction], 2)
                for id_group, id_other_group in list_permutations:
                    if id_other_group in list_linked_group[id_group]:
                        if list_links[id_group][id_other_group] == id_direction:
                            continue
                        merge_group(id_group, id_other_group)
                        return True


                    is_linked = search_links(id_group, id_other_group, {id_mid_point})
                    if is_linked:
                        merge_group(id_group, id_other_group)
                        return True
    return False


def search_links(id_current_mid_point, id_final_mid_point, list_fixed_mid_point):
    """search is two mid points are linked together"""
    for id_linked_mid_point in list_linked_group[id_current_mid_point]:
        if id_linked_mid_point in list_fixed_mid_point:
            continue

        if id_linked_mid_point == id_final_mid_point:
            return True

        list_fixed_mid_point.add(id_linked_mid_point)
        is_linked = search_links(id_current_mid_point, id_final_mid_point, list_fixed_mid_point)
        if is_linked:
            return True

    return False



def get_ordered_mid_point(list_unordered_mid_point):
    list_mid_point_coords = list(zip(*list_unordered_mid_point))
    print(list_mid_point_coords)
    if is_pawn:
        list_distance = [(id_mid_point, mid_point[0]**2 + mid_point[1]**2)
                         for id_mid_point, mid_point in enumerate(list_unordered_mid_point)]
    else:
        mid_point_centre = [sum(list_mid_point_coords[0])/len(list_mid_point_coords[0]),
                            sum(list_mid_point_coords[1])/len(list_mid_point_coords[1])]
        list_distance = [(id_mid_point, (mid_point[0] - mid_point_centre[0])**2 +
                                        (mid_point[1] - mid_point_centre[1])**2)
                         for id_mid_point, mid_point in enumerate(list_unordered_mid_point)]
    list_distance.sort(key=lambda distance: distance[1])
    print("dist", list_distance)
    list_ordered_mid_point = [distance[0] for distance in list_distance]
    return list_ordered_mid_point



def create_loop():
    """determine if there is a loop"""
    list_loop = {}

    for graph in list_graph:
        for id_mid_point in graph:
            list_loop.update({id_mid_point:set()})
        list_permutations = itertools.permutations(range(len(graph)), 2)
        for group_A, group_B in list_permutations:
            if group_A not in list_linked_group[group_B]:
                continue
            list_current_loop = set()
            get_loop(group_B, group_A, (group_B,), list_current_loop)
            list_loop.update({group_A: list_current_loop})
    return list_loop


def get_loop(id_group, group_A, list_blocked_group, list_current_loop):
    """search for loops across all links"""
    for linked_group in list_linked_group[id_group].difference(list_blocked_group):
        if group_A == linked_group and len(list_blocked_group) != 1:
            list_current_loop.add(group_A)
            return True

        is_loop = get_loop(linked_group, group_A,
                           list_blocked_group + (linked_group,), list_current_loop)

        if is_loop:
            list_current_loop.add(id_group)
            return True

    return False


def check_has_two_directions(id_mid_point, list_moved_mid_point):
    """check if a mid point has two links with another mid point"""
    list_linked_moved_mid_point = list(list_moved_mid_point.intersection(
                                                       list_linked_group[id_mid_point]))
    first_direction = list_links[id_mid_point][list_linked_moved_mid_point[0]]
    has_two_directions = False
    for id_moved_mid_point in list_linked_moved_mid_point[1:]:
        if list_links[id_mid_point][id_moved_mid_point] != first_direction:
            has_two_directions = True
            break
    else:
        id_moved_mid_point = None
    return has_two_directions, list_linked_moved_mid_point[0], id_moved_mid_point


def get_intersection_move_direction(id_mid_point, id_first_mid_point, id_second_mid_point,
                                    list_current_mid_point):
    """get the intersection of the first and second mid point
    based on their direction with the mid point"""
    first_mid_point = list_current_mid_point[id_first_mid_point]
    first_direction = list_links[id_mid_point][id_first_mid_point]
    second_mid_point = list_current_mid_point[id_second_mid_point]
    second_direction = list_links[id_mid_point][id_second_mid_point]

    if first_direction > second_direction:
        (first_mid_point, first_direction,
         second_mid_point, second_direction) = (second_mid_point, second_direction,
                                                first_mid_point, first_direction)

    if first_direction == 0:
        x = first_mid_point[0]
        if second_direction == 1:
            y = second_mid_point[1]

        elif second_direction == 2:
            y = second_mid_point[0] + second_mid_point[1] - x

        elif second_direction == 3:
            y = -second_mid_point[0] + second_mid_point[1] + x

    elif first_direction == 1:
        y = first_mid_point[1]
        if second_direction == 2:
            x = second_mid_point[0] + second_mid_point[1] - y

        elif second_direction == 3:
            x = second_mid_point[0] - second_mid_point[1] + y

    elif first_direction == 2 and second_direction == 3:
        x = (first_mid_point[0] + first_mid_point[1] + second_mid_point[0] - second_mid_point[1])/2

        y = -second_mid_point[0] + second_mid_point[1] + x

    else:
        raise Exception

    move = [x - list_current_mid_point[id_mid_point][0],
            y - list_current_mid_point[id_mid_point][1]]

    return move

def align_mid_point():
    """aslign mid points depending of their direction by cancelling their offsets"""
    for graph in list_graph:
        id_mid_point = list(graph)[0]
        if len(list_loop) == 0:
            spread_align_mid_point(id_mid_point, {id_mid_point})
        else:
            spread_align_mid_point_with_loop(id_mid_point, {id_mid_point})


def spread_align_mid_point(id_mid_point, list_moved_mid_point):
    """spread the offset cancel to all linked mid point"""
    list_current_mid_point = deque([id_mid_point])
    while list_current_mid_point:
        id_current_mid_point = list_current_mid_point.popleft()
        for id_linked_mid_point in list_linked_group[id_current_mid_point]:
            if id_linked_mid_point in list_moved_mid_point:
                continue
            list_current_mid_point.append(id_linked_mid_point)
            list_moved_mid_point.add(id_linked_mid_point)

            new_mid_point = get_alignement_mid_point(id_current_mid_point, id_linked_mid_point)
            move = [new_mid_point[0] - list_mid_point[id_linked_mid_point][0],
                    new_mid_point[1] - list_mid_point[id_linked_mid_point][1]]
            list_mid_point[id_linked_mid_point] = new_mid_point
            move_direction(list_group_direction[id_linked_mid_point], move)


def spread_align_mid_point_with_loop(id_mid_point, list_moved_mid_point):
    """spread the offset cancel to all linked mid point when ther is a loop"""
    list_current_mid_point = deque([id_mid_point])
    while list_current_mid_point:
        id_current_mid_point = list_current_mid_point.popleft()
        for id_linked_mid_point in list_linked_group[id_current_mid_point]:
            if id_linked_mid_point in list_moved_mid_point:
                continue
            list_current_mid_point.append(id_linked_mid_point)
            list_moved_mid_point.add(id_linked_mid_point)

            (has_two_directions, id_first_mid_point,
             id_second_mid_point) = check_has_two_directions(id_linked_mid_point,
                                                             list_moved_mid_point)

            if has_two_directions:
                move = get_intersection_move_direction(id_linked_mid_point, id_first_mid_point,
                                                       id_second_mid_point, list_mid_point)

                list_mid_point[id_linked_mid_point][0] += move[0]
                list_mid_point[id_linked_mid_point][1] += move[1]
                move_direction(list_group_direction[id_linked_mid_point], move)
            else:
                new_mid_point = get_alignement_mid_point(id_current_mid_point, id_linked_mid_point)
                move = [new_mid_point[0] - list_mid_point[id_linked_mid_point][0],
                        new_mid_point[1] - list_mid_point[id_linked_mid_point][1]]
                list_mid_point[id_linked_mid_point] = new_mid_point
                move_direction(list_group_direction[id_linked_mid_point], move)


def get_alignement_mid_point(id_mid_point, id_linked_mid_point):
    """get the position of the mid point after the offset is cancelled"""
    direction = list_links[id_mid_point][id_linked_mid_point]
    mid_point = list_mid_point[id_mid_point]
    linked_mid_point = list_mid_point[id_linked_mid_point]

    if direction == 0:
        x = mid_point[0]
        y = linked_mid_point[1]

    elif direction == 1:
        x = linked_mid_point[0]
        y = mid_point[1]

    elif direction == 2:
        x = (mid_point[0] + mid_point[1] - linked_mid_point[1] + linked_mid_point[0])/2
        y = linked_mid_point[1] + x - linked_mid_point[0]


    elif direction == 3:
        x = (mid_point[0] - mid_point[1] + linked_mid_point[1] + linked_mid_point[0])/2
        y = linked_mid_point[1] + linked_mid_point[0] - x


    else:
        return Exception

    return [x, y]



def link_aligned_mid_point():
    """links points that are linked to the same mid point with the same direction but after the
    direction alignement is done to not have huge offset differences in the scaled result"""
    for id_mid_point in range(len(list_mid_point)):
        for id_direction in range(4):
            if len(list_linked_group_per_direction[id_mid_point][id_direction]) >= 2:
                list_permutations = itertools.permutations(
                    list_linked_group_per_direction[id_mid_point][id_direction], 2)
                for id_group, id_other_group in list_permutations:
                    if id_other_group in list_links[id_group].keys():
                        continue


                    list_links[id_group][id_other_group] = id_direction
                    list_linked_group[id_group].add(id_other_group)
                    list_offset[id_group][id_other_group] = (
                        list_offset[id_mid_point][id_other_group] -
                        list_offset[id_mid_point][id_group])


def scale_down_mid_point():
    """scale down all mid points by dividing them by a determined coeff"""
    furthest_coord = max(abs(coord) for coords in list_mid_point for coord in coords)/SCALE

    list_scaled_mid_point = []
    list_scaled_group_direction = copy.deepcopy(list_group_direction)
    for id_mid_point, mid_point in enumerate(list_mid_point):
        new_x = mid_point[0]/furthest_coord
        new_y = mid_point[1]/furthest_coord
        list_scaled_mid_point.append([new_x, new_y])

        move_direction(list_scaled_group_direction[id_mid_point],
                       [new_x - mid_point[0], new_y - mid_point[1]])
    return list_scaled_mid_point, list_scaled_group_direction


def separate_mid_points():
    """main loop of functions to push mid points away from their starting position"""
    global i
    list_current_direction = []
    list_ratio_direction = []

    for id_mid_point, mid_point in enumerate(list_scaled_mid_point):
        list_current_direction.append([[0, 0], [0, 0], [0, 0], [0, 0]])
        move_direction(list_current_direction[-1], mid_point)
        scaled_direction_length = list_scaled_group_direction[id_mid_point]
        scaled_direction_coords = list_current_direction[id_mid_point]
        list_ratio_direction.append([
            [(scaled_direction_length[id_direction][0] -
              scaled_direction_coords[id_direction][0])/PRECISION,
             (scaled_direction_length[id_direction][1] -
              scaled_direction_coords[id_direction][1])/PRECISION]
            for id_direction in range(4)])
    print("original", list_scaled_mid_point, list_current_direction, list_ratio_direction)
    for i in range(PRECISION):
        for id_mid_point in list_ordered_mid_point:
            for id_axis, axis in enumerate(list_current_direction[id_mid_point]):
                axis[0] += list_ratio_direction[id_mid_point][id_axis][0]
                axis[1] += list_ratio_direction[id_mid_point][id_axis][1]

            if i%step == 0:
                list_store_data[int(i/step)][0].append(list_scaled_mid_point[id_mid_point][0])
                list_store_data[int(i/step)][1].append(list_scaled_mid_point[id_mid_point][1])

        for id_mid_point in list_ordered_mid_point:
            push_line_of_sight(id_mid_point, list_current_direction)

    return list_current_direction


def move_direction(current_direction, move):
    """move the directions according to the move"""
    current_direction[0][0] += move[0]
    current_direction[0][1] += move[0]
    current_direction[1][0] += move[1]
    current_direction[1][1] += move[1]
    current_direction[2][0] += move[0] + move[1]
    current_direction[2][1] += move[0] + move[1]
    current_direction[3][0] += move[0] - move[1]
    current_direction[3][1] += move[0] - move[1]


def push_line_of_sight(id_mid_point, list_current_direction):
    """push the mid point based on the directions of the other mid point"""
    current_direction = list_current_direction[id_mid_point]
    for id_other_mid_point in range(len(list_scaled_mid_point)):
        if id_other_mid_point == id_mid_point:
            continue
        current_other_direction = list_current_direction[id_other_mid_point]
        """calculate the move"""
        list_moved_direction = set()
        while True:
            line_of_sight = get_line_of_sight(id_mid_point, id_other_mid_point,
                                             list_moved_direction.union({
                                                 list_links[id_mid_point].get(
                                                     id_other_mid_point)}),
                                             list_scaled_mid_point, list_current_direction)
            if line_of_sight == None:
                break
            list_moved_direction.add(line_of_sight)
            push_direction = list_relative_position[id_mid_point][
                                                        id_other_mid_point][line_of_sight]
            if line_of_sight == 0:
                if push_direction == 1:
                    move = [current_direction[0][1] - current_other_direction[0][0], 0]

                else:
                    move = [current_direction[0][0] - current_other_direction[0][1], 0]

            elif line_of_sight == 1:
                if push_direction == 1:
                    move = [0, current_direction[1][1] - current_other_direction[1][0]]

                else:
                    move = [0, current_direction[1][0] - current_other_direction[1][1]]

            elif line_of_sight == 2:
                if push_direction == 1:
                    direction_distance = (current_direction[2][1] -
                                          current_other_direction[2][0])/2

                else:
                    direction_distance = (current_direction[2][0] -
                                          current_other_direction[2][1])/2

                move = [direction_distance, direction_distance]

            elif line_of_sight == 3:
                """the calculations are backwards but this direction is done backwards"""
                if push_direction == 1:
                    direction_distance = (current_direction[3][1] -
                                          current_other_direction[3][0])/2
                else:
                    direction_distance = (current_direction[3][0] -
                                          current_other_direction[3][1])/2

                move = [direction_distance, -direction_distance]

            else:
                raise Exception

            """apply the move the the mid point"""
            if id_other_mid_point in list_mid_point_graph[id_mid_point]:
                 move, list_fixed_mid_point = get_push_move_change(id_mid_point,
                                                                   id_other_mid_point,
                                                                   move, line_of_sight)
            else:
                list_fixed_mid_point = [id_other_mid_point]
            if move == [0, 0]:
                continue
            print("push", i, move, id_mid_point, id_other_mid_point,
                  line_of_sight , push_direction,
                  list_fixed_mid_point,
                   list_scaled_mid_point[id_mid_point],
                   list_scaled_mid_point[id_other_mid_point],
                    current_direction,
                    current_other_direction,
                    list_links[id_mid_point].get(
                        id_other_mid_point, 10))
            list_scaled_mid_point[id_other_mid_point][0] += move[0]
            list_scaled_mid_point[id_other_mid_point][1] += move[1]
            move_direction(list_current_direction[id_other_mid_point], move)

            spread_mid_point_push_move(id_other_mid_point, id_mid_point, line_of_sight,
                                       push_direction,
                                       set(list_fixed_mid_point), move, list_current_direction)

def get_line_of_sight(id_mid_point, id_other_mid_point, list_moved_direction,
                      list_current_mid_point, list_current_direction):
    """determine if a mid point is in one of the directions of another one"""
    mid_point = list_current_mid_point[id_mid_point]
    other_mid_point = list_current_mid_point[id_other_mid_point]


    for id_direction in range(4):
        if id_direction in list_moved_direction:
            continue

        if id_direction == 0:
            mid_point_direction = mid_point[0]
            other_mid_point_direction = other_mid_point[0]

        elif id_direction == 1:
            mid_point_direction = mid_point[1]
            other_mid_point_direction = other_mid_point[1]

        elif id_direction == 2:
            mid_point_direction = mid_point[0] + mid_point[1]
            other_mid_point_direction = other_mid_point[0] + other_mid_point[1]

        elif id_direction == 3:
            mid_point_direction = mid_point[0] - mid_point[1]
            other_mid_point_direction = other_mid_point[0] - other_mid_point[1]

        else:
            raise Exception

        if mid_point_direction < other_mid_point_direction:
            biggest_direction = max(list_current_direction[id_mid_point][id_direction][1] -
                                        mid_point_direction,
                                    other_mid_point_direction -
                                        list_current_direction[id_other_mid_point][id_direction][0])
            if mid_point_direction + biggest_direction >= other_mid_point_direction:
                return id_direction

        else:
            biggest_direction = max(mid_point_direction -
                                        list_current_direction[id_mid_point][id_direction][0],
                                    list_current_direction[id_other_mid_point][id_direction][1] -
                                        other_mid_point_direction)
            if mid_point_direction + biggest_direction <= other_mid_point_direction:
                return id_direction



def get_push_move_change(id_mid_point, id_other_mid_point, move, line_of_sight):
    """get the change in move due to the links between the mid points"""
    list_fixed_mid_point = get_fixed_path(id_mid_point, id_other_mid_point)
    direction = list_links[id_other_mid_point][list_fixed_mid_point[-2]]
    if direction in [0, 1]:
        opposite_direction = 1 - direction
    else:
        opposite_direction = 5 - direction

    if direction == line_of_sight:
        return [0, 0], list_fixed_mid_point

    elif opposite_direction == line_of_sight:
        return move, list_fixed_mid_point

    elif direction == 0:
        move = [0, move[1]]

    elif direction == 1:
        move = [move[0], 0]

    elif direction == 2:
        if line_of_sight == 0:
            move = [move[0], -move[0]]

        elif line_of_sight == 1:
            move = [-move[1], move[1]]

        else:
            raise Exception

    elif direction == 3:
        if line_of_sight == 0:
            move = [move[0], move[0]]

        elif line_of_sight == 1:
            move = [move[1], move[1]]

        else:
            raise Exception

    return move, list_fixed_mid_point



def get_fixed_path(id_mid_point, id_searched_mid_point):
    """find the shortest path from a point to another"""
    list_moved_mid_point = {id_mid_point}
    list_current_path = [(id_mid_point, [id_mid_point])]
    while list_current_path:
        id_current_mid_point, path = list_current_path.pop()

        for id_linked_mid_point in list_linked_group[id_current_mid_point]:
            if id_linked_mid_point in list_moved_mid_point:
                continue

            if id_linked_mid_point == id_searched_mid_point:
                return path + [id_linked_mid_point]

            list_moved_mid_point.add(id_linked_mid_point)
            list_current_path.insert(0, (id_linked_mid_point, path + [id_linked_mid_point]))





def spread_mid_point_push_move(id_moved_mid_point, id_push_mid_point, line_of_sight,
                               push_direction, list_fixed_mid_point, move, list_current_direction):
    """determine how to spread the move caused by the direction of another mid point"""
    if id_push_mid_point not in list_mid_point_graph[id_moved_mid_point]:
        list_free_mid_point = set()
        for id_graph_mid_point in list_mid_point_graph[id_moved_mid_point]:
            if list_relative_position[id_push_mid_point][
                            id_graph_mid_point][line_of_sight] == push_direction:
                list_free_mid_point.add(id_graph_mid_point)
        list_moved_mid_point = {id_push_mid_point, id_moved_mid_point}
        list_shifted_mid_point = list_linked_group[id_moved_mid_point].difference(
                                                                            list_free_mid_point)
        move_shifted_mid_point(list_shifted_mid_point, id_moved_mid_point,
                                   line_of_sight, move, list_moved_mid_point,
                                   list_current_direction)


        spread_push_move(id_moved_mid_point, list_free_mid_point, line_of_sight, push_direction,
                         move, list_moved_mid_point, list_current_direction)


    else:
        list_moved_mid_point = {id_push_mid_point, id_moved_mid_point}
        list_free_mid_point = set()
        get_free_mid_point(id_moved_mid_point, id_push_mid_point, list_moved_mid_point,
                           line_of_sight, push_direction, list_free_mid_point,
                           list_current_direction)

        list_shifted_mid_point = list_linked_group[id_moved_mid_point].difference(
                                    list_free_mid_point).difference(list_moved_mid_point)
        print("spread", id_push_mid_point, id_moved_mid_point, line_of_sight, push_direction,
                  list_free_mid_point, list_moved_mid_point, move, list_shifted_mid_point)
        move_shifted_mid_point(list_shifted_mid_point, id_moved_mid_point,
                                   line_of_sight, move, list_moved_mid_point,
                                   list_current_direction)
        spread_push_move(id_moved_mid_point, list_free_mid_point, line_of_sight, push_direction,
                         move, list_moved_mid_point, list_current_direction)


def spread_push_move(id_moved_mid_point, list_free_mid_point, line_of_sight, push_direction, move,
                     list_moved_mid_point, list_current_direction):
    """spread the move caused by the direction of another mid point"""
    list_current_mid_point = deque([id_moved_mid_point])
    while list_current_mid_point:
        id_current_mid_point = list_current_mid_point.popleft()
        for id_free_mid_point in list_linked_group[id_current_mid_point]:
            if (id_free_mid_point in list_moved_mid_point or
                id_free_mid_point not in list_free_mid_point):
                continue
            list_current_mid_point.append(id_free_mid_point)
            list_moved_mid_point.add(id_free_mid_point)

            print("free", id_free_mid_point ,move)

            (has_two_directions, id_first_mid_point,
             id_second_mid_point) = check_has_two_directions(id_free_mid_point,
                                                             list_moved_mid_point)
            print("direction", has_two_directions, id_free_mid_point, list_moved_mid_point)
            if has_two_directions:
                move = get_intersection_move_direction(id_free_mid_point, id_first_mid_point,
                                                       id_second_mid_point, list_scaled_mid_point)
                print("intersection", id_free_mid_point, move)

            list_scaled_mid_point[id_free_mid_point][0] += move[0]
            list_scaled_mid_point[id_free_mid_point][1] += move[1]
            move_direction(list_current_direction[id_free_mid_point], move)

            list_shifted_mid_point = list_linked_group[id_free_mid_point].difference(
                                                list_free_mid_point.union(list_moved_mid_point))
            move_shifted_mid_point(list_shifted_mid_point, id_free_mid_point,
                                       line_of_sight, move, list_moved_mid_point,
                                       list_current_direction)


def move_shifted_mid_point(list_shifted_mid_point, id_free_mid_point, line_of_sight, move,
                           list_moved_mid_point, list_current_direction):
    """move shifted mid points"""
    for id_shifted_mid_point in list_shifted_mid_point:
        (has_two_directions, id_first_mid_point,
         id_second_mid_point) = check_has_two_directions(id_shifted_mid_point, list_moved_mid_point)
        print("check", list_linked_group[id_free_mid_point], id_shifted_mid_point,
              list_shifted_mid_point, list_moved_mid_point, has_two_directions)
        if has_two_directions:
            move = get_intersection_move_direction(id_shifted_mid_point, id_first_mid_point,
                                                   id_second_mid_point, list_scaled_mid_point)

            list_scaled_mid_point[id_shifted_mid_point][0] += move[0]
            list_scaled_mid_point[id_shifted_mid_point][1] += move[1]
            move_direction(list_current_direction[id_shifted_mid_point], move)

        else:
            move = get_shifted_move(id_shifted_mid_point, id_free_mid_point,
                                    line_of_sight, move, list_moved_mid_point,
                                    list_current_direction)

            list_scaled_mid_point[id_shifted_mid_point][0] += move[0]
            list_scaled_mid_point[id_shifted_mid_point][1] += move[1]
            move_direction(list_current_direction[id_shifted_mid_point], move)


def get_shifted_move(id_shifted_mid_point, id_free_mid_point, line_of_sight, move,
                           list_moved_mid_point, list_current_direction):
    """get the move of a shifted mid point"""
    list_moved_mid_point.add(id_shifted_mid_point)
    direction = list_links[id_free_mid_point][id_shifted_mid_point]
    if direction in [0, 1]:
        opposite_direction = 1 - direction
    else:
        opposite_direction = 5 - direction

    if direction == line_of_sight:

        raise Exception(direction, line_of_sight, id_free_mid_point, id_shifted_mid_point)

    elif opposite_direction == line_of_sight:
        move = [0, 0]

    elif line_of_sight == 0:
        if direction == 2:
            move = [0, move[1]]

        elif direction == 3:
            move = [0, -move[1]]

    elif line_of_sight == 1:
        if direction == 2:
            move = [move[0], 0]

        elif direction == 3:
            move = [-move[0], 0]

    elif line_of_sight == 2 or line_of_sight == 3:
        if direction == 0:
            move = [move[0], -move[1]]

        elif direction == 1:
            move = [-move[0], move[1]]

    print("shift", id_shifted_mid_point, move, direction, line_of_sight)
    return move


def get_free_mid_point(id_moved_mid_point, id_push_mid_point, list_moved_mid_point,
                       line_of_sight, push_direction, list_free_mid_point, list_current_direction):
    """get the linked mid points that are in the same side of the push caused by a direction"""
    list_current_mid_point = deque([id_moved_mid_point])
    while list_current_mid_point:
        id_current_mid_point = list_current_mid_point.popleft()
        for id_linked_mid_point in list_linked_group[id_current_mid_point]:
            if (id_linked_mid_point in list_moved_mid_point or
                id_linked_mid_point in list_free_mid_point or
                id_linked_mid_point in list_links[id_push_mid_point].keys()):
                continue
            list_current_mid_point.append(id_linked_mid_point)
            if list_relative_position[id_push_mid_point][
                    id_linked_mid_point][line_of_sight] == push_direction:
                list_free_mid_point.add(id_linked_mid_point)


def spread_integer_mid_point_move():
    """move the mid points so that their final move vector from the start has integer coordinates"""
    list_integer_move = {id_mid_point: ([0, 0], False)
                         for id_mid_point in range(len(list_scaled_mid_point))}
    list_moved_mid_point = set()
    print(list_integer_move)
    for graph in list_graph:
        for id_mid_point in list_ordered_mid_point:
            if id_mid_point in graph:
                break
        else:
            raise Exception
        list_moved_mid_point.add(id_mid_point)

        mid_point = list_scaled_mid_point[id_mid_point]
        old_mid_point = list_old_mid_point[id_mid_point]

        if (abs(math.modf(mid_point[0] - old_mid_point[0])[0]) <
            abs(math.modf(mid_point[0] + old_mid_point[0])[0])):
            move = [abs(math.modf(mid_point[0] - old_mid_point[0])[0])]
        else:
            move = [-abs(math.modf(mid_point[0] + old_mid_point[0])[0])]

        if (abs(math.modf(mid_point[1] - old_mid_point[1])[0]) <
            abs(math.modf(mid_point[1] + old_mid_point[1])[0])):
            move.append(abs(math.modf(mid_point[1] - old_mid_point[1])[0]))
        else:
            move.append(-abs(math.modf(mid_point[1] + old_mid_point[1])[0]))

        list_integer_move.update({id_mid_point: (move, True)})
        mid_point[0] += move[0]
        mid_point[1] += move[1]
        move_direction(list_current_direction[id_mid_point], move)

        """parity check"""
        if (sum(list_scaled_mid_point[id_mid_point]) -
            sum(list_old_mid_point[id_mid_point])) % 2 == 1:
            if (abs(list_scaled_mid_point[id_mid_point][0]) >
                abs(list_scaled_mid_point[id_mid_point][1])):
                mid_point[0] += math.copysign(1, mid_point[0])
                move_direction(list_current_direction[id_mid_point],
                               [math.copysign(1, mid_point[0]), 0])
            else:
                mid_point[1] += math.copysign(1, mid_point[1])
                move_direction(list_current_direction[id_mid_point],
                               [0, math.copysign(1, mid_point[0])])

        if len(list_loop) == 0:
            spread_integer(id_mid_point, list_moved_mid_point, list_integer_move)

        else:
            spread_integer_with_loop(id_mid_point, list_moved_mid_point, list_integer_move)

def spread_integer(id_mid_point, list_moved_mid_point, list_integer_move):
    """spread the integer spread to all linked mid points"""
    list_current_mid_point = deque([id_mid_point])
    while list_current_mid_point:

        id_current_mid_point = list_current_mid_point.popleft()
        print("f", id_current_mid_point)
        for id_linked_mid_point in list_linked_group[id_current_mid_point]:
            if id_linked_mid_point in list_moved_mid_point:
                continue
            list_current_mid_point.append(id_linked_mid_point)
            list_moved_mid_point.add(id_linked_mid_point)
            move_integer_mid_point(id_current_mid_point, id_linked_mid_point, list_integer_move)


def spread_integer_with_loop(id_mid_point, list_moved_mid_point, list_integer_move):
    """spread the integer spread to all linked mid points when there is a loop"""
    list_current_mid_point = deque([id_mid_point])
    while list_current_mid_point:
        id_current_mid_point = list_current_mid_point.popleft()
        for id_linked_mid_point in list_ordered_mid_point:
            if (id_linked_mid_point not in list_linked_group[id_current_mid_point] or
                id_linked_mid_point in list_moved_mid_point):
                continue
            list_current_mid_point.append(id_linked_mid_point)
            list_moved_mid_point.add(id_linked_mid_point)
            (has_two_directions, id_first_mid_point,
                 id_second_mid_point) = check_has_two_directions(id_linked_mid_point,
                                                                 list_moved_mid_point)
            print("mid_point", id_linked_mid_point, has_two_directions, id_first_mid_point,
                  id_second_mid_point)
            if has_two_directions:
                intersection = get_intersection_move(id_linked_mid_point, id_first_mid_point,
                                                     id_second_mid_point, list_scaled_mid_point)
                move = [intersection[0] - list_scaled_mid_point[id_linked_mid_point][0],
                        intersection[1] - list_scaled_mid_point[id_linked_mid_point][1]]
                list_integer_move.update({id_mid_point: (move, True)})
                list_scaled_mid_point[id_linked_mid_point] = intersection
                move_direction(list_current_direction[id_linked_mid_point], move)

            else:
                move_integer_mid_point(id_current_mid_point, id_linked_mid_point, list_integer_move)


def get_closest_direction(id_mid_point, direction):
    """get the mid point which has the closest direction"""
    id_closest_mid_point = None
    id_closest_direction = None
    closest_direction = None
    for id_other_mid_point in range(len(list_scaled_mid_point)):
        if (id_other_mid_point == id_mid_point or
            id_other_mid_point in list_linked_group[id_mid_point]):
            continue
        current_direction = list_current_direction[id_mid_point]
        current_other_direction = list_current_direction[id_other_mid_point]
        list_direction = [abs(current_direction[id_direction][side] -
                              current_other_direction[id_direction][side])
                                  for id_direction in [0, 1]
                                  for side in range(2)] + [
                          abs(current_direction[id_direction][side] -
                              current_other_direction[id_direction][side])/sqrt2
                                  for id_direction in [2, 3]
                                  for side in range(2)]


        del list_direction[direction]
        current_closest_direction = min(list_direction)
        id_current_closest_direction = list_direction.index(current_closest_direction)
        if id_current_closest_direction >= direction:
            id_current_closest_direction += 1

        if id_closest_mid_point == None or current_closest_direction < closest_direction:
            id_closest_mid_point = id_other_mid_point
            id_closest_direction = id_current_closest_direction
            closest_direction = current_closest_direction

    if id_closest_mid_point == None:
        """take the closest mid point by coordinate instead"""
        id_closest_distance = None
        for id_other_mid_point, other_mid_point in enumerate(list_scaled_mid_point):
            if id_other_mid_point == id_mid_point:
                continue
            if (id_closest_distance == None or
                other_mid_point[0]**2 + other_mid_point[1]**2 < id_closest_distance):
                id_closest_mid_point = id_other_mid_point
                id_closest_distance = other_mid_point[0]**2 + other_mid_point[1]**2

    return id_closest_mid_point, id_closest_direction



def move_integer_mid_point(id_fixed_mid_point, id_current_mid_point, list_integer_move):
    """move the mid point according to its links
    so that the final move vector has integer coordinates"""
    fixed_mid_point = list_scaled_mid_point[id_fixed_mid_point]
    current_mid_point = list_scaled_mid_point[id_current_mid_point]
    old_mid_point = list_old_mid_point[id_current_mid_point]
    direction = list_links[id_current_mid_point][id_fixed_mid_point]
    offset = list_offset[id_current_mid_point][id_fixed_mid_point]

    id_closest_mid_point, id_closest_direction = get_closest_direction(id_current_mid_point,
                                                                       direction)
    print("direction", direction, id_current_mid_point, id_fixed_mid_point)
    saved_mid_point = current_mid_point.copy()
    if direction == 0:
        current_mid_point[0] = fixed_mid_point[0] + offset
        if list_integer_move[id_closest_mid_point][0][1] > 0:
            current_mid_point[1] += abs(math.modf(current_mid_point[1] - old_mid_point[1])[0])

            if (sum(current_mid_point) - sum(old_mid_point)) % 2 == 1:
                current_mid_point[1] += 1


        elif list_integer_move[id_closest_mid_point][0][1] == 0:
            current_mid_point[1] += abs(math.modf(current_mid_point[1] - old_mid_point[1])[0])

            if (sum(current_mid_point) - sum(old_mid_point)) % 2 == 1:
                current_mid_point[1] -= 1

        else:
            current_mid_point[1] -= abs(math.modf(current_mid_point[1] + old_mid_point[1])[0])

            if (sum(current_mid_point) - sum(old_mid_point)) % 2 == 1:
                current_mid_point[1] -= 1

        move = [current_mid_point[0] - saved_mid_point[0],
                current_mid_point[1] - saved_mid_point[1]]

        list_integer_move.update({id_current_mid_point: (move, True)})
        move_direction(list_current_direction[id_current_mid_point], move)
        recalibrate_integer_move(id_current_mid_point, id_fixed_mid_point, direction,
                                 3, move, [0, 2], list_integer_move)


    elif direction == 1:
        current_mid_point[1] = fixed_mid_point[1] + offset

        if list_integer_move[id_closest_mid_point][0][0] > 0:
            current_mid_point[0] += abs(math.modf(current_mid_point[0] - old_mid_point[0])[0])

            if (sum(current_mid_point) - sum(old_mid_point)) % 2 == 1:
                current_mid_point[0] += 1


        elif list_integer_move[id_closest_mid_point][0][0] == 0:
            current_mid_point[0] += abs(math.modf(current_mid_point[0] - old_mid_point[0])[0])

            if (sum(current_mid_point) - sum(old_mid_point)) % 2 == 1:
                current_mid_point[0] -= 1

        else:
            current_mid_point[0] -= abs(math.modf(current_mid_point[0] + old_mid_point[0])[0])

            if (sum(current_mid_point) - sum(old_mid_point)) % 2 == 1:
                current_mid_point[0] -= 1

        move = [current_mid_point[0] - saved_mid_point[0],
                current_mid_point[1] - saved_mid_point[1]]

        print("move", move)
        list_integer_move.update({id_current_mid_point: (move, True)})
        move_direction(list_current_direction[id_current_mid_point], move)
        recalibrate_integer_move(id_current_mid_point, id_fixed_mid_point, direction,
                                 None, move, [2, 0], list_integer_move)



    elif direction == 2:
        current_mid_point[0] = fixed_mid_point[0] + offset/2
        current_mid_point[1] = fixed_mid_point[1] + offset/2

        if (list_integer_move[id_closest_mid_point][0][0] -
            list_integer_move[id_closest_mid_point][0][1]) == 0:

            if id_closest_mid_point in list_links[id_current_mid_point]:
                if direction == [0, 1]:
                    other_direction = 1 - direction
                else:
                    other_direction = 5 - direction
                is_down_left_push = list_relative_position[id_current_mid_point][
                                            id_closest_mid_point][other_direction] == -1

            else:
                if list_relative_position[id_current_mid_point][
                                          id_closest_mid_point][direction] == 1:
                    is_down_left_push = (list_integer_move[id_closest_mid_point][0][0] +
                                         list_integer_move[id_closest_mid_point][0][1]) > 0
                else:
                    is_down_left_push = (list_integer_move[id_closest_mid_point][0][0] +
                                         list_integer_move[id_closest_mid_point][0][1]) < 0

        else:
            is_down_left_push = (list_integer_move[id_closest_mid_point][0][0] -
                                 list_integer_move[id_closest_mid_point][0][1]) > 0



        if is_down_left_push:
            current_mid_point[0] += abs(math.modf(current_mid_point[0] - old_mid_point[0])[0])
            current_mid_point[1] -= abs(math.modf(current_mid_point[1] + old_mid_point[1])[0])
            if (current_mid_point[0] - old_mid_point[0] !=
                int(current_mid_point[0] - old_mid_point[0])):
                current_mid_point[0] += 0.5
                current_mid_point[1] -= 0.5

        else:
            current_mid_point[0] -= abs(math.modf(current_mid_point[0] + old_mid_point[0])[0])
            current_mid_point[1] += abs(math.modf(current_mid_point[1] - old_mid_point[1])[0])
            if (current_mid_point[0] - old_mid_point[0] !=
                int(current_mid_point[0] - old_mid_point[0])):
                current_mid_point[0] -= 0.5
                current_mid_point[1] += 0.5

        move = [current_mid_point[0] - saved_mid_point[0],
                current_mid_point[1] - saved_mid_point[1]]

        list_integer_move.update({id_current_mid_point: (move, True)})
        move_direction(list_current_direction[id_current_mid_point], move)
        recalibrate_integer_move(id_current_mid_point, id_fixed_mid_point, direction,
                                 1, move, [1, -1], list_integer_move)


    elif direction == 3:
        current_mid_point[0] = fixed_mid_point[0] + offset/2
        current_mid_point[1] = fixed_mid_point[1] - offset/2

        if (list_integer_move[id_closest_mid_point][0][0] +
            list_integer_move[id_closest_mid_point][0][1]) == 0:

            if id_closest_mid_point in list_links[id_current_mid_point]:
                if direction == [0, 1]:
                    other_direction = 1 - direction
                else:
                    other_direction = 5 - direction
                is_up_right_push = list_relative_position[id_current_mid_point][
                                            id_closest_mid_point][other_direction] == 1

            else:
                if list_relative_position[id_current_mid_point][
                                          id_closest_mid_point][direction] == 1:
                    is_up_right_push = (list_integer_move[id_closest_mid_point][0][0] -
                                         list_integer_move[id_closest_mid_point][0][1]) > 0
                else:
                    is_up_right_push = (list_integer_move[id_closest_mid_point][0][0] -
                                         list_integer_move[id_closest_mid_point][0][1]) < 0

        else:
            is_up_right_push = (list_integer_move[id_closest_mid_point][0][0] -
                                 list_integer_move[id_closest_mid_point][0][1]) > 0


        if is_up_right_push:
            current_mid_point[0] += abs(math.modf(current_mid_point[0] - old_mid_point[0])[0])
            current_mid_point[1] += abs(math.modf(current_mid_point[1] - old_mid_point[1])[0])
            if (current_mid_point[0] - old_mid_point[0] !=
                int(current_mid_point[0] - old_mid_point[0])):
                current_mid_point[0] += 0.5
                current_mid_point[1] += 0.5
        else:
            current_mid_point[0] -= abs(math.modf(current_mid_point[0] + old_mid_point[0])[0])
            current_mid_point[1] -= abs(math.modf(current_mid_point[1] + old_mid_point[1])[0])
            if (current_mid_point[0] - old_mid_point[0] !=
                int(current_mid_point[0] - old_mid_point[0])):
                current_mid_point[0] -= 0.5
                current_mid_point[1] -= 0.5

        move = [current_mid_point[0] - saved_mid_point[0],
                current_mid_point[1] - saved_mid_point[1]]

        list_integer_move.update({id_current_mid_point: (move, True)})
        move_direction(list_current_direction[id_current_mid_point], move)
        recalibrate_integer_move(id_current_mid_point, id_fixed_mid_point, direction,
                                 3, move, [1, 1], list_integer_move)


def recalibrate_integer_move(id_mid_point, id_linked_mid_point, direction, inverted_direction,
                             move, change_move, list_integer_move):
    for id_other_mid_point in range(len(list_scaled_mid_point)):
        if id_other_mid_point == id_mid_point or not list_integer_move[id_other_mid_point][1]:
            continue

        while True:
            line_of_sight = get_line_of_sight(
                id_other_mid_point, id_mid_point,
                {direction, list_links[id_other_mid_point].get(id_mid_point)},
                list_scaled_mid_point, list_current_direction)
            if line_of_sight == None:
                if direction in [0, 1]:
                    opposite_direction = 1 - direction
                else:
                    opposite_direction = 5 - direction

                push_opposite_direction = list_relative_position[id_mid_point][
                                                        id_linked_mid_point][opposite_direction]
                if push_opposite_direction > 0:
                    push_move = change_move
                else:
                    push_move = [-change_move[0], -change_move[1]]

                list_integer_move.update({id_mid_point: ([move[0] + change_move[0],
                                                          move[1] + change_move[1]], True)})
                list_scaled_mid_point[id_mid_point][0] += push_move[0]
                list_scaled_mid_point[id_mid_point][1] += push_move[1]
                move_direction(list_current_direction[id_mid_point], push_move)

                for id_test_mid_point in range(len(list_scaled_mid_point)):
                    if id_test_mid_point == id_mid_point:
                        continue
                    is_line_of_sight = get_line_of_sight(id_test_mid_point, id_mid_point,
                        {direction, list_links[id_test_mid_point].get(id_mid_point)},
                        list_scaled_mid_point, list_current_direction)
                    if is_line_of_sight != None:
                        list_integer_move.update({id_mid_point: (move, True)})
                        list_scaled_mid_point[id_mid_point][0] -= push_move[0]
                        list_scaled_mid_point[id_mid_point][1] -= push_move[1]
                        move_direction(list_current_direction[id_mid_point],
                                        [-push_move[0], -push_move[1]])
                        break
                else:
                    continue

                break

            else:
                break

        while True:
            line_of_sight = get_line_of_sight(
                id_other_mid_point, id_mid_point,
                {direction, list_links[id_other_mid_point].get(id_mid_point)},
                list_scaled_mid_point, list_current_direction)
            print("recalibrate", id_other_mid_point,
                  change_move, line_of_sight,
                                              list_scaled_mid_point[id_other_mid_point],
                                              list_scaled_mid_point[id_mid_point],
                                              list_current_direction[id_other_mid_point],
                                              list_current_direction[id_mid_point],)
            if line_of_sight == None:
                wrong_relative_position = get_wrong_relative_position(id_mid_point,
                                                                      [id_other_mid_point],
                                                                      list_scaled_mid_point)
                if wrong_relative_position != None:
                    line_of_sight = wrong_relative_position
                else:
                    break

            push_direction = list_relative_position[id_other_mid_point][
                                                    id_mid_point][line_of_sight]

            if line_of_sight == inverted_direction:
                push_direction = -push_direction

            print("moved", move, list_scaled_mid_point[id_mid_point],
                  list_scaled_mid_point[id_other_mid_point],
                  list_relative_position[id_mid_point][id_other_mid_point])
            if push_direction < 0:
                change_move[0] = -change_move[0]
                change_move[1] = -change_move[1]


            list_scaled_mid_point[id_mid_point][0] += change_move[0]
            list_scaled_mid_point[id_mid_point][1] += change_move[1]
            print("passed", change_move)
            if get_wrong_relative_position(id_mid_point, [id_other_mid_point],
                                           list_scaled_mid_point) != None:
                list_scaled_mid_point[id_mid_point][0] -= change_move[0]
                list_scaled_mid_point[id_mid_point][1] -= change_move[1]
                break

            else:
                move[0] += change_move[0]
                move[1] += change_move[1]
                list_integer_move.update({id_mid_point: (move, True)})
                move_direction(list_current_direction[id_mid_point], change_move)


def get_wrong_relative_position(id_mid_point, list_moved_mid_point, list_current_mid_point):
    mid_point = list_current_mid_point[id_mid_point]
    for id_moved_mid_point in list_moved_mid_point:
        if id_moved_mid_point == id_mid_point:
            continue
        moved_mid_point = list_current_mid_point[id_moved_mid_point]
        for direction, relative_position in list_relative_position[id_mid_point][
                                                                   id_moved_mid_point].items():
            if direction == 0:
                if relative_position == 1:
                    if mid_point[0] > moved_mid_point[0]:
                        return direction
                else:
                    if mid_point[0] < moved_mid_point[0]:
                        return direction

            elif direction == 1:
                if relative_position == 1:
                    if mid_point[1] > moved_mid_point[1]:
                        return direction
                else:
                    if mid_point[1] < moved_mid_point[1]:
                        return direction

            elif direction == 2:
                if relative_position == 1:
                    if mid_point[0] + mid_point[1] > moved_mid_point[0] + moved_mid_point[1]:
                        return direction
                else:
                    if mid_point[0] + mid_point[1] < moved_mid_point[0] + moved_mid_point[1]:
                        return direction

            elif direction == 3:
                if relative_position == 1:
                    if mid_point[0] - mid_point[1] > moved_mid_point[0] - moved_mid_point[1]:
                        return direction
                else:
                    if mid_point[0] - mid_point[1] < moved_mid_point[0] - moved_mid_point[1]:
                        return direction

    return None

def get_intersection_move(id_mid_point, id_first_mid_point, id_second_mid_point,
                          list_current_mid_point):
    """get the intersection of the first and second mid point
    based on their direction with the mid point considering their relative offsets"""

    first_mid_point = list_current_mid_point[id_first_mid_point]
    first_direction = list_links[id_mid_point][id_first_mid_point]
    first_offset = list_offset[id_mid_point][id_first_mid_point]
    second_mid_point = list_current_mid_point[id_second_mid_point]
    second_direction = list_links[id_mid_point][id_second_mid_point]
    second_offset = list_offset[id_mid_point][id_second_mid_point]

    if first_direction > second_direction:
        (first_mid_point, first_direction, first_offset,
         second_mid_point, second_direction, second_offset) = (
                                             second_mid_point, second_direction, second_offset,
                                             first_mid_point, first_direction, first_offset)

    if first_direction == 0:
        x = first_mid_point[0] + first_offset
        if second_direction == 1:
            y = second_mid_point[1] + second_offset

        elif second_direction == 2:
            y = second_mid_point[0] + second_mid_point[1] + second_offset - x

        elif second_direction == 3:
            y = second_mid_point[0] - second_mid_point[1] + second_offset + x

    elif first_direction == 1:
        y = first_mid_point[1] + first_offset
        if second_direction == 2:
            x = second_mid_point[0] + second_mid_point[1] + second_offset - y

        elif second_direction == 3:
            x = second_mid_point[0] - second_mid_point[1] + second_offset + y



    elif first_direction == 2 and second_direction == 3:
        x = (second_mid_point[0] - second_offset/2 +
            (first_mid_point[0] + first_mid_point[1] + first_offset -
             second_mid_point[1] - second_offset/2))/2

        y = -second_mid_point[0] + second_mid_point[1] + second_offset + x

    else:
        raise Exception

    return [x, y]


def get_list_linked_ordered_mid_point():
    list_linked_ordered_mid_point = [list_ordered_mid_point[0]]
    list_path = {list_ordered_mid_point[0]: [list_ordered_mid_point[0]]}
    for id_mid_point in list_ordered_mid_point[1:]:
        if id_mid_point in list_path:
            continue
        list_moved_mid_point = {list_ordered_mid_point[0]}
        list_current_path = collections.deque()
        list_current_path.append((id_mid_point, [id_mid_point]))
        while list_current_path:
            id_current_mid_point, path = list_current_path.popleft()
            for id_linked_mid_point in list_linked_group[id_current_mid_point]:
                if id_current_mid_point in list_moved_mid_point:
                    continue

                if id_linked_mid_point == list_ordered_mid_point[0]:
                    path.append(list_ordered_mid_point[0])
                    for i, id_fixed_mid_point in enumerate(path):
                        if id_fixed_mid_point not in list_linked_ordered_mid_point:
                            list_linked_ordered_mid_point.append(id_fixed_mid_point)
                            list_path.update({id_fixed_mid_point: path[i:]})
                    break

                list_moved_mid_point.add(id_linked_mid_point)
                list_current_path.append((id_linked_mid_point, path + [id_linked_mid_point]))

    return list_linked_ordered_mid_point, list_path


def simple_push():
    list_current_mid_point = collections.defaultdict(lambda: [0, 0])
    list_current_direction = []
    for id_mid_point, mid_point in enumerate(list_mid_point):
        group_direction = list_group_direction[id_mid_point]
        list_current_direction.append([[group_direction[0][0] - mid_point[0],
                                        group_direction[0][1] - mid_point[0]],
                                       [group_direction[1][0] - mid_point[1],
                                        group_direction[1][1] - mid_point[1]],
                                       [group_direction[2][0] - (mid_point[0] + mid_point[1]),
                                        group_direction[2][1] - (mid_point[0] + mid_point[1])],
                                       [group_direction[3][0] - (mid_point[0] - mid_point[1]),
                                        group_direction[3][1] - (mid_point[0] - mid_point[1])]])


    list_linked_ordered_mid_point, list_path = get_list_linked_ordered_mid_point()
    list_moved_mid_point = {list_linked_ordered_mid_point[0]}
    print(list_linked_ordered_mid_point)
    for id_mid_point in list_linked_ordered_mid_point[1:]:
        list_moved_mid_point.add(id_mid_point)
        id_linked_mid_point = list_path[id_mid_point][1]
        direction = list_links[id_mid_point][id_linked_mid_point]
        offset = list_offset[id_mid_point][id_linked_mid_point]
        mid_point = list_current_mid_point[id_mid_point]
        linked_mid_point = list_current_mid_point[id_linked_mid_point]
        old_mid_point = list_old_mid_point[id_mid_point]

        if id_mid_point in list_loop:
            (has_two_directions, id_first_mid_point,
             id_second_mid_point) = check_has_two_directions(id_mid_point, list_moved_mid_point)
            if has_two_directions:
                intersection = get_intersection_move(id_mid_point, id_first_mid_point,
                                                     id_second_mid_point, list_current_mid_point)
                move = [intersection[0] - mid_point[0],
                        intersection[1] - mid_point[1]]
                list_current_mid_point[id_mid_point] = intersection
                move_direction(list_current_direction[id_mid_point], move)

                if get_wrong_relative_position(id_mid_point, list_moved_mid_point,
                                               list_current_mid_point) != None:
                    return False
                continue

        if direction in [0, 1]:
            opposite_direction = 1 - direction
        else:
            opposite_direction = 5 - direction

        push_direction = list_relative_position[id_linked_mid_point][
                                                id_mid_point][opposite_direction]

        list_furthest_direction = []
        saved_mid_point = mid_point.copy()
        for list_mid_point_direction in zip(*[list_current_direction[id_moved_mid_point]
                                              for id_moved_mid_point in list_moved_mid_point]):
            list_direction = list(zip(*list_mid_point_direction))
            list_furthest_direction.append([min(list_direction[0]),
                                            max(list_direction[1])])
        if direction == 0:
            mid_point[0] = linked_mid_point[0] + offset
            if push_direction == 1:
                mid_point[1] = max(list_furthest_direction[2][1] - mid_point[0],
                                             -list_furthest_direction[3][0] + mid_point[0]
                                    ) + SIMPLE_PUSH_PADDING
                mid_point[1] += abs(math.modf(old_mid_point[1] - mid_point[1])[0])

                if (sum(old_mid_point) - sum(mid_point)) % 2 != 1:
                    mid_point[1] += 1

            else:
                mid_point[1] = min(list_furthest_direction[2][0] - mid_point[0],
                                       -list_furthest_direction[3][1] + mid_point[0]
                                   ) - SIMPLE_PUSH_PADDING
                mid_point[1] -= abs(math.modf(old_mid_point[1] + mid_point[1])[0])

                if (sum(old_mid_point) - sum(mid_point)) % 2 == 1:
                    mid_point[1] -= 1



        elif direction == 1:
            mid_point[1] = linked_mid_point[1] + offset
            if push_direction == 1:
                mid_point[0] = max(list_furthest_direction[2][1] - mid_point[1],
                                             list_furthest_direction[3][1] + mid_point[1]
                                   ) + SIMPLE_PUSH_PADDING
                mid_point[0] += abs(math.modf(old_mid_point[0] - mid_point[0])[0])
                if (sum(old_mid_point) - sum(mid_point)) % 2 == 1:
                    mid_point[0] += 1

            else:
                mid_point[0] = min(list_furthest_direction[2][0] - mid_point[1],
                                       list_furthest_direction[3][0] + mid_point[1]
                                   ) - SIMPLE_PUSH_PADDING
                mid_point[0] -= abs(math.modf(old_mid_point[0] + mid_point[0])[0])

                if (sum(old_mid_point) - sum(mid_point)) % 2 == 1:
                    mid_point[0] -= 1


        elif direction == 2:
            mid_point[0] = linked_mid_point[0] + offset/2
            mid_point[1] = linked_mid_point[1] + offset/2
            if push_direction == 1:
                cardinal_move_length = abs(max(list_furthest_direction[0][1] - mid_point[0],
                                           -list_furthest_direction[1][0] + mid_point[1]) * sqrt2
                                           ) + SIMPLE_PUSH_PADDING

                mid_point[0] += cardinal_move_length/sqrt2
                mid_point[0] += abs(math.modf(mid_point[0] - old_mid_point[0])[0])
                mid_point[1] -= cardinal_move_length/sqrt2
                mid_point[1] -= abs(math.modf(mid_point[1] - old_mid_point[1])[0])

                if old_mid_point[0] - mid_point[0] != int(old_mid_point[0] - mid_point[0]):
                    mid_point[0] += 0.5
                    mid_point[1] -= 0.5

            else:
                cardinal_move_length = abs(min(list_furthest_direction[0][0] - mid_point[0],
                                           -list_furthest_direction[1][1] + mid_point[1]) * sqrt2
                                           ) + SIMPLE_PUSH_PADDING

                mid_point[0] -= cardinal_move_length
                mid_point[0] -= abs(math.modf(mid_point[0] + old_mid_point[0])[0])
                mid_point[1] += cardinal_move_length
                mid_point[1] += abs(math.modf(mid_point[1] - old_mid_point[1])[0])

                if old_mid_point[0] - mid_point[0] != int(old_mid_point[0] - mid_point[0]):
                    mid_point[0] -= 0.5
                    mid_point[1] += 0.5

        elif direction == 3:
            mid_point[0] = linked_mid_point[0] + offset/2
            mid_point[1] = linked_mid_point[1] - offset/2
            if push_direction == 1:
                cardinal_move_length = abs(max(list_furthest_direction[0][1] - mid_point[0],
                                               list_furthest_direction[1][1] - mid_point[1]) * sqrt2
                                           ) + SIMPLE_PUSH_PADDING
                mid_point[0] += cardinal_move_length
                mid_point[0] += abs(math.modf(mid_point[0] - old_mid_point[0])[0])
                mid_point[1] += cardinal_move_length
                mid_point[1] += abs(math.modf(mid_point[1] - old_mid_point[1])[0])

                if old_mid_point[0] - mid_point[0] != int(old_mid_point[0] - mid_point[0]):
                    mid_point[0] += 0.5
                    mid_point[1] += 0.5
            else:
                cardinal_move_length = abs(min(list_furthest_direction[0][0] - mid_point[0],
                                               list_furthest_direction[1][0] - mid_point[1]) * sqrt2
                                           ) + SIMPLE_PUSH_PADDING
                mid_point[0] -= cardinal_move_length
                mid_point[0] -= abs(math.modf(mid_point[0] + old_mid_point[0])[0])
                mid_point[1] -= cardinal_move_length
                mid_point[1] -= abs(math.modf(mid_point[1] + old_mid_point[1])[0])

                if old_mid_point[0] - mid_point[0] != int(old_mid_point[0] - mid_point[0]):
                    mid_point[0] -= 0.5
                    mid_point[1] -= 0.5

        move = [mid_point[0] - saved_mid_point[0], mid_point[1] - saved_mid_point[1]]
        move_direction(list_current_direction[id_mid_point], move)
        if get_wrong_relative_position(id_mid_point, list_moved_mid_point,
                                       list_current_mid_point) != None:
            print(list_moved_mid_point, list_current_mid_point)
            return False

    return list_current_mid_point


def centre_graph():
    """put the main board in the centre or make all the mid points around the centre"""
    if is_pawn:
        centre_vector = (list_old_mid_point[0][0] - list_scaled_mid_point[0][0],
                         list_old_mid_point[0][1] - list_scaled_mid_point[0][1])

    else:
        group_mid_point = (sum([mid_point[0] for mid_point in list_scaled_mid_point])
                                 /len(list_scaled_mid_point),
                           sum([mid_point[1] for mid_point in list_scaled_mid_point])
                                 /len(list_scaled_mid_point))
        group_mid_point_dist = [(group_mid_point[0] - mid_point[0])**2 +
                             (group_mid_point[1] - mid_point[1])**2
                             for mid_point in list_scaled_mid_point]
        closest_group = group_mid_point_dist.index(min(group_mid_point_dist))
        centre_vector = (-round(list_scaled_mid_point[closest_group][0]),
                         -round(list_scaled_mid_point[closest_group][1]))
    for mid_point in list_scaled_mid_point:
            mid_point[0] += centre_vector[0]
            mid_point[1] += centre_vector[1]


def get_pieces_locations():
    """turn the mid point location into their respective pieces locations"""
    new_infinite_board_piece = {}
    for id_mid_point, (old_mid_point, new_mid_point) in enumerate(zip(list_old_mid_point,
                                                                    list_scaled_mid_point)):
        vector_mid_point = (new_mid_point[0] - old_mid_point[0],
                            new_mid_point[1] - old_mid_point[1])
        for piece_coords, piece_type in list_group[id_mid_point].items():
            new_piece_coords = (round(piece_coords[0] + 4.5 + vector_mid_point[0]),
                                round(piece_coords[1] + 4.5 + vector_mid_point[1]))
            new_infinite_board_piece.update({new_piece_coords: piece_type})
    return new_infinite_board_piece


def scale_up_move_piece(moved_piece, id_move_direction, id_target_direction, id_target_group):
    """allows you to move a piece in the modified version of the board"""
    if id_target_direction == id_move_direction:
        raise ValueError("the target direction cannot be the same as the move direction")

    vector = [list_scaled_mid_point[id_target_group][0] - list_old_mid_point[id_target_group][0],
              list_scaled_mid_point[id_target_group][1] - list_old_mid_point[id_target_group][1]]

    if id_move_direction == 0:
        if id_target_direction == 1:
            move = [0, vector[1]]

        elif id_target_direction == 2:
            move = [0, vector[0] + vector[1]]

        elif id_target_direction == 3:
            move = [0, -vector[0] + vector[1]]

    if id_move_direction == 1:
        if id_target_direction == 0:
            move = [vector[0], 0]

        elif id_target_direction == 2:
            move = [vector[0] + vector[1], 0]

        elif id_target_direction == 3:
            move = [vector[0] - vector[1], 0]

    if id_move_direction == 2:
        if id_target_direction == 0:
            move = [vector[0], -vector[0]]

        elif id_target_direction == 1:
            move = [-vector[1], vector[1]]

        elif id_target_direction == 3:
            move = [-(vector[0] - vector[1])/2, (vector[0] - vector[1])/2]


    if id_move_direction == 3:
        if id_target_direction == 0:
            move = [vector[0], vector[0]]

        elif id_target_direction == 1:
            move = [vector[1], vector[1]]

        elif id_target_direction == 2:
            move = [(vector[0] + vector[1])/2, (vector[0] + vector[1])/2]

    new_moved_piece = [moved_piece[0] + move[0], moved_piece[1] + move[1]]

    return new_moved_piece


sqrt2 = 1.4142135623730951
PRECISION = 100
BASE_AXIS_LEN = 2
GROUP_PADDING = 2
SIMPLE_PUSH_PADDING = 1
SCALE = 3
OFFSET_COEFF = 0.5

if __name__ == "__main__":
    infinite_board_pieces = convert_board_notation_to_long_format("""
    [Event "Casual local Classical infinite chess game"] [Site "https://www.infinitechess.org/"] [Variant "Classical"] [Round "-"] [UTCDate "2025.03.02"] [UTCTime "23:17:58"] [TimeControl "-"]  b 15/100 7 (8|1) P1,2+|P2,2+|P3,2+|P4,2+|P5,2+|P6,2+|P7,2+|P8,2+|p1,7+|p2,7+|p3,7+|p4,7+|p5,7+|p6,7+|p7,7+|p8,7+|R1,1+|r1,8+|r8,8+|N2,1|N7,1|n2,8|B3,1|B6,1|b3,8|b6,8|K5,1+|k5,8+|q4,37|Q50,0|n7,8|R39,37
                                                                  """)

    if "p" in infinite_board_pieces.values() or "P" in infinite_board_pieces.values():
        is_pawn = True
    else:
        is_pawn = False

    list_group, list_mid_point = create_groups()
    print(list_mid_point)
    while True:
        list_group_direction = furthest_pieces()
        (is_two_directions, list_links, list_relative_position,
         list_linked_group, list_linked_group_per_direction,
         list_graph, list_mid_point_graph, list_offset) = create_links()

        if is_two_directions or is_parallel_linked_direction():
            continue

        break

    list_old_mid_point = copy.deepcopy(list_mid_point)
    if len(list_group) != 1:
        list_loop = create_loop()
        list_ordered_mid_point = get_ordered_mid_point(list_mid_point)

        if len(list_graph) == 1:
            list_simple_mid_point = False
            #list_simple_mid_point = simple_push()

        else:
            list_simple_mid_point = False

        if list_simple_mid_point == False:
            align_mid_point()
            list_scaled_mid_point, list_scaled_group_direction = scale_down_mid_point()


            step = 1
            list_store_data = [[[], []] for i in range(int(PRECISION/step))]
            list_current_direction = separate_mid_points()

            print(list_scaled_mid_point)
            link_aligned_mid_point()
            spread_integer_mid_point_move()
        else:
            list_scaled_mid_point = [list_simple_mid_point[id_mid_point]
                                     for id_mid_point in range(len(list_mid_point))]
    else:
        list_scaled_mid_point = list_mid_point

    centre_graph()

    new_infinite_board_piece = get_pieces_locations()
    print(new_infinite_board_piece)
    new_board = convert_long_format_to_board_notation(new_infinite_board_piece)
    print(new_board)